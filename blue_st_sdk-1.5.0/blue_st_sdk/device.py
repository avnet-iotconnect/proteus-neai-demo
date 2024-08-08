################################################################################
# COPYRIGHT(c) 2024 STMicroelectronics                                         #
#                                                                              #
# Redistribution and use in source and binary forms, with or without           #
# modification, are permitted provided that the following conditions are met:  #
#   1. Redistributions of source code must retain the above copyright notice,  #
#      this list of conditions and the following disclaimer.                   #
#   2. Redistributions in binary form must reproduce the above copyright       #
#      notice, this list of conditions and the following disclaimer in the     #
#      documentation and/or other materials provided with the distribution.    #
#   3. Neither the name of STMicroelectronics nor the names of its             #
#      contributors may be used to endorse or promote products derived from    #
#      this software without specific prior written permission.                #
#                                                                              #
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"  #
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE    #
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE   #
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE    #
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR          #
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF         #
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS     #
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN      #
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)      #
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE   #
# POSSIBILITY OF SUCH DAMAGE.                                                  #
################################################################################


"""device

The device module is responsible for managing a Bluetooth Low Energy (BLE)
device and allocating the needed resources.
"""


# IMPORT

from abc import ABCMeta
from abc import abstractmethod
from bluepy.btle import Peripheral
from bluepy.btle import DefaultDelegate
from bluepy.btle import BTLEException
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import Enum
import logging
import struct
import time

from blue_st_sdk.utils.stl_to_transport_protocol import STL2TransportProtocol
from blue_st_sdk.advertising_data.blue_st_advertising_data import BlueSTProtocol
from blue_st_sdk.advertising_data.blue_st_advertising_data_parser import BlueSTAdvertisingDataParser
from blue_st_sdk.virtualization.virtualization_manager import VirtualizationManager
from blue_st_sdk.utils.ble_device_definitions import Debug
from blue_st_sdk.utils.ble_device_definitions import Config
from blue_st_sdk.utils.ble_device_definitions import FeatureCharacteristic
from blue_st_sdk.utils.ble_device_definitions import TIMESTAMP_OFFSET_BYTES
from blue_st_sdk.utils.blue_st_exceptions import BlueSTInvalidAdvertisingDataException
from blue_st_sdk.utils.blue_st_exceptions import BlueSTInvalidOperationException
from blue_st_sdk.utils.blue_st_exceptions import BlueSTInvalidDataException
from blue_st_sdk.utils.uuid_to_feature_map import UUIDToFeatureMap
from blue_st_sdk.utils.number_conversion import LittleEndian
from blue_st_sdk.utils.unwrap_timestamp import UnwrapTimestamp
from blue_st_sdk.debug_console import DebugConsole
from blue_st_sdk.utils.python_utils import lock


# CLASSES

class Device(Peripheral, object):
    """Bluetooth Low Energy device class.

    This class allows exporting features using Bluetooth Low Energy (BLE)
    transmission.
    """

    _NOTIFICATION_ON = struct.pack("BB", 0x01, 0x00)
    """Notifications ON."""

    _NOTIFICATION_OFF = struct.pack("BB", 0x00, 0x00)
    """Notifications OFF."""

    _NUMBER_OF_THREADS = 5
    """Number of threads to be used to notify the listeners."""

    DELAY_CONNECT_SET_MTU_s = 0.5
    """Delay needed between the connect() and the setMTU() calls of
    the bluepy library."""

    def __init__(self, scan_entry, manager):
        """Constructor.

        Args:
            scan_entry (ScanEntry): BLE device as built by the bluepy library.
            It contains device information and advertising data. Refer to
            `ScanEntry <https://ianharvey.github.io/bluepy-doc/scanentry.html>`_
            for more information.
            manager (:class:`blue_st_sdk.manager.Manager`): The BLE manager
            that has created the device.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidAdvertisingDataException`
            is raised if the advertising data is not well formed.
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
            is raised if the operation requested is not supported.
        """
        # Creating an un-connected "Peripheral" object.
        # It is needed to call the "connect()" method on this object (passing a
        # device address) before it will be usable.
        try:
            with lock(self):
                Peripheral.__init__(self)
        except BTLEException as e:
            raise BlueSTInvalidOperationException('Bluetooth invalid operation.')

        self._friendly_name = None
        """Friendly name."""

        self._status = DeviceStatus.INIT
        """Status."""

        self._thread_pool = ThreadPoolExecutor(Device._NUMBER_OF_THREADS)
        """Pool of thread used to notify the listeners."""

        self._listeners = []
        """List of listeners to the device changes.
        It is a thread safe list, so a listener can subscribe itself through a
        callback."""

        self._scan_entry = scan_entry
        """BLE device."""

        self._manager = manager
        """BLE manager."""

        self._rssi = self._scan_entry.rssi
        """Received Signal Strength Indication (RSSI) for the last received
        broadcast from the device. This is an integer value measured in dB,
        where 0 dB is the maximum (theoretical) signal strength, and more
        negative numbers indicate a weaker signal."""

        self._last_rssi_update = datetime.now()
        """Last update to the Received Signal Strength Indication."""

        self._mtu_bytes = STL2TransportProtocol.DEFAULT_MTU_SIZE_bytes
        """MTU size."""

        self._connectable = self._scan_entry.connectable
        """The device may accept direct connections."""

        self._advertising_data = None
        """Advertising data."""

        self._declared_features = []
        """List of the declared features.
        The way features are declared depends on the version of the BlueST
        protocol adopted:
        - BlueST protocol v1 declares the features through four bytes within
        the advertising data;
        - BlueST protocol v2 declares them through a device model that is
        referenced by the device-id and the firmware-id identifiers;
        - BlueST protocol vLE does not support features.
        No duplicates."""

        self._implemented_features = []
        """List of the implemented features.
        No duplicates."""

        self._feature_mask_to_feature_dict = {}
        """Mask to feature dictionary: there is an entry for each one-bit-high
        32-bit mask."""

        self._external_uuid_to_features_dict = UUIDToFeatureMap()
        """UUID to list of external features dictionary: there is an entry for
        each list of declared external features.
        Note: A UUID may export more than one feature."""

        self._update_char_handle_to_features_dict = {}
        """Characteristic's handle to list of features dictionary: it tells
        which features to update when new data from a characteristic are
        received.
        Note: A UUID may export more than one feature.
        Note: The same feature may be added to different list of features in
              case more characteristics have the same corresponding bit set to
              high.
        Note: BlueSTSDK_Android: mCharFeatureMap."""

        self._char_handle_to_characteristic_dict = {}
        """Characteristic's handle to characteristic dictionary."""

        self._unwrap_timestamp = UnwrapTimestamp()
        """Unwrap timestamp reference."""

        self._debug_console = None
        """Debug console used to read/write debug messages from/to the Bluetooth
        device. None if the device doesn't export the debug service."""

        # Command Caracteristic.
        self._command_characteristic = None

        # Device entry from the device catalog.
        self._device_entry = None

        # Device model.
        self._device_model = None

    def build(self):
        """Parse the information got by the bluepy library and
        build the list of features.
        
        This method has to be called just after the construction and
        before any use of the object.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidAdvertisingDataException`
            is raised if the advertising data is not well formed.
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
            is raised if this method is not run as root.
        """

        # Updating device.
        self._update_device_status(DeviceStatus.IDLE)

        # Extract information from the received BLE data.
        try:
            with lock(self):
                self._advertising_data = BlueSTAdvertisingDataParser.parse(
                    self._scan_entry.getScanData())
        except BlueSTInvalidAdvertisingDataException as e:
            raise e
        except BTLEException as e:
            raise BlueSTInvalidOperationException('Bluetooth invalid operation.')

        # Building features.
        try:
            self._build_features_upon_advertisement()
        except BlueSTInvalidOperationException as e:
            raise e

    def __str__(self):
        """Return a string that describes the device.

        Returns:
            str: A string that describes the device.
        """
        #return str(self.get_advertising_data())
        if not self.get_advertising_data():
            return "[ MAC:{} | RSSI[db]: {} ]".format(
                self.get_mac_address(),
                self.get_rssi()
            )
        elif self.get_advertising_data().get_protocol_version() == BlueSTProtocol.BLUEST_v1_PROTOCOL.value:
            return "[ Name: {} | MAC:{} | RSSI[db]: {} | Connectable: {} | BlueST: v1 | IDs: {} | Feature mask: {} ]".format(
                self.get_advertising_data().get_name(),
                self.get_mac_address(),
                self.get_rssi(),
                self.is_connectable(),
                hex(self.get_advertising_data().get_device_id()),
                hex(self.get_advertising_data().get_feature_mask())
            )
        elif self.get_advertising_data().get_protocol_version() == BlueSTProtocol.BLUEST_v2_PROTOCOL.value:
            return "[ Name: {} | MAC:{} | RSSI[db]: {} | Connectable: {} | BlueST: v2 | IDs: {} | Option bytes: {} ]".format(
                self.get_advertising_data().get_name(),
                self.get_mac_address(),
                self.get_rssi(),
                self.is_connectable(),
                (hex(self.get_advertising_data().get_device_id()),
                hex(self.get_advertising_data().get_firmware_id())),
                self.get_advertising_data().get_option_bytes()
            )
        elif self.get_advertising_data().get_protocol_version() == BlueSTProtocol.BLUEST_vLE_PROTOCOL.value:
            return "[ Name: {} | MAC:{} | RSSI[db]: {} | Connectable: {} | BlueST: vLE | IDs: {} | Payload: {} Decoded: {} ]".format(
                self.get_advertising_data().get_name(),
                self.get_mac_address(),
                self.get_rssi(),
                self.is_connectable(),
                (hex(self.get_advertising_data().get_device_id()),
                hex(self.get_advertising_data().get_firmware_id()),
                hex(self.get_advertising_data().get_payload_id())),
                self.get_advertising_data().get_option_bytes(),
                self._manager.decode_bluest_le(self.get_advertising_data())
            )

    def _build_feature_from_class(self, feature_class):
        """Get a feature object from the given class.

        Args:
            feature_class (class): Feature class to instantiate.
        
        Returns:
            :class:`blue_st_sdk.feature.Feature`: The feature object built if
            the feature class is valid, "None" otherwise.
        """
        return feature_class(self) if feature_class else None

    def _build_features_upon_advertisement(self):
        """Build the features that the device declares in the advertising data.
        It is used by BlueST protocol v1 and v2.

        The way they are declared depends on the version of the BlueST protocol
        implemented.
        BlueST protocol v1 declares the features through four bytes within the
        advertising data.
        BlueST protocol v2 declares them through a device model that is
        referenced by the device-id and the firmware-id identifiers.
        BlueST protocol vLE does not support features.
        No duplicates.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
            is raised if the operation requested is not supported.
        """
        try:
            # Getting information from advertising data.
            protocol_version = self._advertising_data.get_protocol_version()
            device_id = self._advertising_data.get_device_id()

            # Initializing list of declared features and mask-to-feature
            # dictionary.
            self._declared_features = []
            self._feature_mask_to_feature_dict = {}

            # Building the features.
            if protocol_version == BlueSTProtocol.BLUEST_v1_PROTOCOL.value:

                # Getting the dictionary that maps feature-masks to feature-classes
                # related to the advertising data's device identifier.
                #features_decoder = blue_st_sdk.manager.Manager.get_device_features(device_id)

                # Getting features mask from the advertisement data.
                features_mask = self._advertising_data.get_feature_mask()

                # Building base features.
                self._build_base_features_upon_advertisement(features_mask, protocol_version)

            elif protocol_version == BlueSTProtocol.BLUEST_v2_PROTOCOL.value:

                # Creating Virtualization Manager.
                virtualization_manager = VirtualizationManager.instance()
                #virtualization_manager_listener = MyVirtualizationManagerListener()
                #virtualization_manager.add_listener(virtualization_manager_listener)

                # Retrieving information about the device from the device catalog.
                self._device_entry = virtualization_manager.get_device_entry(
                    self.get_advertising_data().get_device_id(),
                    self.get_advertising_data().get_firmware_id())

                # Building features as declared by the device catalog.
                # Note: "firmware_id" equal to "FF" means the firmware is a custom one.
                if self._device_entry:
                    characteristics = self._device_entry['characteristics']
                    for characteristic in characteristics:
                        # Printing characteristic declared in device catalog.
                        logging.getLogger('BlueST').debug('Characteristic declared: {}'.format(characteristic))

                        # Extracting the feature mask from the characteristic's UUID.
                        feature_mask = FeatureCharacteristic.extract_feature_mask(characteristic['uuid'])

                        # Getting the dictionaries that map feature-masks to feature-classes
                        # related to all the features available.
                        base_features_decoder = FeatureCharacteristic.BASE_MASK_TO_FEATURE_DICT.copy()
                        extended_features_decoder = FeatureCharacteristic.EXTENDED_MASK_TO_FEATURE_DICT.copy()

                        # Building features.
                        if FeatureCharacteristic.declares_base_features(characteristic['uuid']):
                            self._build_base_features_upon_advertisement(feature_mask, protocol_version)
                        elif FeatureCharacteristic.declares_extended_features(characteristic['uuid']):
                            self._build_extended_features_upon_advertisement(feature_mask)

                # Retrieving device model from the Internet.
                if self._device_entry:
                    if 'dtmi' in self._device_entry:
                        self._device_model = virtualization_manager.get_device_model(
                            self._device_entry['dtmi'])

        except BlueSTInvalidOperationException as e:
            raise e

    def _build_base_features_upon_advertisement(self, features_mask, protocol_version):
        """Build the base features of a BLE characteristic.
        It is used by BlueST protocol v1 and v2.

        Args:
            features_mask (int): Mask of features declared by a characteristic.
            protocol_version (:class:`blue_st_sdk.advertising_data.blue_st_advertising_data.BlueSTProtocol`):
            The version of the BlueST protocol.
        """
        try:
            # Getting the dictionaries that map feature-masks to feature-classes
            # related to all the features available.
            base_features_decoder = FeatureCharacteristic.BASE_MASK_TO_FEATURE_DICT.copy()

            # Build the features.
            # Looking for the declared features in reverse order to get them in
            # the correct order in case of a characteristic that exports multiple
            # features.
            features = []
            feature_mask = 1 << 31
            for i in range(0, 32):
                if (features_mask & feature_mask) != 0:
                    feature = None
                    if feature_mask not in self._feature_mask_to_feature_dict:
                        feature_class = base_features_decoder.get(feature_mask)
                        if feature_class:
                            feature = self._build_feature_from_class(feature_class)
                            self._feature_mask_to_feature_dict[feature_mask] = feature
                            self._declared_features.append(feature)
                            # Printing feature declared in the advertisement.
                            if protocol_version == BlueSTProtocol.BLUEST_v1_PROTOCOL.value:
                                logging.getLogger('BlueST').debug('Feature declared: {}'.format(feature))
                feature_mask = feature_mask >> 1

        except BTLEException as e:
            self._unexpected_disconnect()

    def _build_extended_features_upon_advertisement(self, feature_mask):
        """Build the base features of a BLE characteristic.
        It is used by BlueST protocol v2.

        Args:
            features_mask (int): Mask of features declared by a characteristic.
        """
        try:
            # Getting the dictionaries that map feature-masks to feature-classes
            # related to all the features available.
            extended_features_decoder = FeatureCharacteristic.EXTENDED_MASK_TO_FEATURE_DICT.copy()

            # Build the features.
            feature_class = extended_features_decoder.get(feature_mask)
            if feature_class:
                feature = self._build_feature_from_class(feature_class)
                self._feature_mask_to_feature_dict[feature_mask] = feature #COLLISIONS IN BlueST protocol v2, to be solved.
                self._declared_features.append(feature)

        except BTLEException as e:
            self._unexpected_disconnect()

    def _build_base_features_upon_connection(self, characteristic):
        """Build the base features of a BLE characteristic.
        It is used by BlueST protocol v1 and v2.

        After building the features, add them to the dictionary of the features
        to be updated.

        Args:
            characteristic (Characteristic): The BLE characteristic. Refer to
            `Characteristic <https://ianharvey.github.io/bluepy-doc/characteristic.html>`_
            for more information.
        """
        try:
            # Getting the dictionaries that map feature-masks to feature-classes
            # related to all the features available.
            base_features_decoder = FeatureCharacteristic.BASE_MASK_TO_FEATURE_DICT.copy()

            # Extracting the features mask from the characteristic's UUID.
            features_mask = FeatureCharacteristic.extract_feature_mask(
                characteristic.uuid)

            # Build the features.
            # Looking for the declared features in reverse order to get them in
            # the correct order in case of a characteristic that exports multiple
            # features.
            features = []
            feature_mask = 1 << 31
            for i in range(0, 32):
                if (features_mask & feature_mask) != 0:
                    feature = None
                    if feature_mask in self._feature_mask_to_feature_dict:
                        feature = self._feature_mask_to_feature_dict[feature_mask]
                    else:
                        feature_class = base_features_decoder.get(feature_mask)
                        if feature_class:
                            feature = self._build_feature_from_class(feature_class)
                            self._feature_mask_to_feature_dict[feature_mask] = feature #COLLISIONS IN BlueST protocol v2, to be solved.
                            self._implemented_features.append(feature)
                    if feature:
                        feature.set_enable(True)
                        features.append(feature)
                feature_mask = feature_mask >> 1

            # If the features are valid, add an entry for the corresponding
            # characteristic.
            if features:
                with lock(self):
                    self._update_char_handle_to_features_dict[
                        characteristic.getHandle()] = features

        except BTLEException as e:
            self._unexpected_disconnect()

    def _build_extended_features_upon_connection(self, characteristic, feature_classes):
        """Build the extended features of a BLE characteristic.
        It is used by BlueST protocol v2.

        After building the features, add them to the dictionary of the features
        to be updated.

        Args:
            characteristic (Characteristic): The BLE characteristic. Refer to
            `Characteristic <https://ianharvey.github.io/bluepy-doc/characteristic.html>`_
            for more information.
            feature_classes (list): The list of feature-classes to instantiate.
        """
        # Extracting the feature mask from the characteristic's UUID.
        feature_mask = FeatureCharacteristic.extract_feature_mask(
            characteristic.uuid)

        # Build the features.
        features = []
        for feature_class in feature_classes:
            feature = None
            if feature_mask in self._feature_mask_to_feature_dict:
                feature = self._feature_mask_to_feature_dict[feature_mask]
            else:
                feature = self._build_feature_from_class(feature_class)
                self._feature_mask_to_feature_dict[feature_mask] = feature #COLLISIONS IN BlueST protocol v2, to be solved.
                self._implemented_features.append(feature)
            if feature:
                feature.set_enable(True)
                features.append(feature)

        # If the features are valid, add an entry for the corresponding
        # characteristic.
        try:
            if features:
                with lock(self):
                    self._update_char_handle_to_features_dict[
                        characteristic.getHandle()] = features
        except BTLEException as e:
            self._unexpected_disconnect()

    def _build_external_features_upon_connection(self, characteristic, feature_classes):
        """Build the external features of a BLE characteristic.
        It is used by BlueST protocol v1 in case of external features
        added manually to the device prior to connecting to it.

        After building the features, add them to the dictionary of the features
        to be updated.

        Args:
            characteristic (Characteristic): The BLE characteristic. Refer to
            `Characteristic <https://ianharvey.github.io/bluepy-doc/characteristic.html>`_
            for more information.
            feature_classes (list): The list of feature-classes to instantiate.
        """
        self._build_extended_features_upon_connection(characteristic, feature_classes)


    def _set_features_characteristics(self):
        """For each implemented feature stores a reference to its
        characteristic.

        It is useful to enable/disable notifications on the characteristic
        itself.

        By design, the characteristic that offers more features beyond the
        feature is selected.
        """
        for feature in self._implemented_features:
            features_size = 0
            for entry in self._update_char_handle_to_features_dict.items():
                char_handle = entry[0]
                features = entry[1]
                if feature in features:
                    if not feature._characteristic:
                        feature._characteristic = \
                            self._char_handle_to_characteristic_dict[char_handle]
                        features_size = len(features)
                    else:
                        if len(features) > features_size:
                            feature._characteristic = \
                                self._char_handle_to_characteristic_dict[char_handle]
                            features_size = len(features)

    def _update_features(self, char_handle, data, notify_update=False):
        """Update the features related to a given characteristic.

        Args:
            char_handle (int): The characteristic's handle to look for.
            data (str): The data read from the given characteristic.
            notify_update (bool, optional): If True all the registered listeners
            are notified about the new data.

        Returns:
            bool: True if the characteristic has some features associated to it
            and they have been updated, False otherwise.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidDataException`
            if the data array has not enough data to read.
        """
        # Getting the features corresponding to the given characteristic.
        features = self._get_corresponding_features(char_handle)
        if not features:
            return False

        # Computing the timestamp.
        timestamp = self._unwrap_timestamp.unwrap(
            LittleEndian.bytes_to_uint16(data))

        # Updating the features.
        offset = TIMESTAMP_OFFSET_BYTES
        try:
            for feature in features:
                offset += feature.update(timestamp, data, offset, notify_update)
        except BlueSTInvalidDataException as e:
            raise e
        return True

    def _get_corresponding_features(self, char_handle):
        """Get the features corresponding to the given characteristic.

        Args:
            char_handle (int): The characteristic's handle to look for.

        Returns:
            list: The list of features associated to the given characteristic,
            None if the characteristic does not exist.
        """
        if char_handle in self._update_char_handle_to_features_dict:
            return self._update_char_handle_to_features_dict[char_handle]
        return None

    def _update_device_status(self, new_status, unexpected=False):
        """Update the status of the device.

        Args:
            new_status (:class:`blue_st_sdk.device.DeviceStatus`): New status.
            unexpected (bool, optional): True if the new status is unexpected,
                False otherwise.
        """
        old_status = self._status
        self._status = new_status
        for listener in self._listeners:
            # Calling user-defined callback.
            # self._thread_pool.submit(
            #     listener.on_status_change(
            #         self, new_status.value, old_status.value))
            if new_status == DeviceStatus.CONNECTED:
                self._thread_pool.submit(
                    listener.on_connect(self))
            elif new_status == DeviceStatus.IDLE:
                self._thread_pool.submit(
                    listener.on_disconnect(self, unexpected))

    def _build_debug_console(self, debug_service):
        """Build a debug console used to read/write debug messages from/to the
        Bluetooth device.

        Args:
            debug_service (Service): The BLE service. Refer to
            `Service <https://ianharvey.github.io/bluepy-doc/service.html>`_
            for more information.

        Returns:
            :class:`blue_st_sdk.debug_console.DebugConsole`: A debug console
            used to read/write debug messages from/to the Bluetooth device.
            None if the device doesn't export the needed characteristics.
        """
        try:
            stdinout = None
            stderr = None
            with lock(self):
                characteristics = debug_service.getCharacteristics()
            for characteristic in characteristics:
                if str(characteristic.uuid) == \
                    str(Debug.DEBUG_STDINOUT_BLUESTSDK_SERVICE_UUID):
                    stdinout = characteristic
                elif str(characteristic.uuid) == \
                    str(Debug.DEBUG_STDERR_BLUESTSDK_SERVICE_UUID):
                    stderr = characteristic
                if stdinout and stderr:
                    return DebugConsole(self, stdinout, stderr)
            return None
        except BTLEException as e:
            self._unexpected_disconnect()

    def _unexpected_disconnect(self):
        """Handle an unexpected disconnection."""
        try:
            # Disconnecting.
            self._update_device_status(DeviceStatus.UNREACHABLE)
            with lock(self):
                super(Device, self).disconnect()
            self._update_device_status(DeviceStatus.IDLE, True)
        except BTLEException as e:
            pass

    def connect(self, user_defined_features=None):
        """Open a connection to the device.

        Please note that there is no supervision timeout API within the SDK,
        hence it is not possible to detect immediately an unexpected
        disconnection; it is detected and notified via listeners as soon as a
        read/write/notify operation is executed on the device (limitation
        intrinsic to the bluepy library).

        Args:
            user_defined_features (dict, optional): User-defined feature to be
            added.

        Returns:
            bool: True if the connection to the device has been successful, False
            otherwise.
        """
        try:
            if not self._status == DeviceStatus.IDLE:
                return False

            # Initializing list of implemented features and mask-to-feature
            # dictionary.
            self._implemented_features = []
            self._feature_mask_to_feature_dict = {}

            # Creating a delegate object, which is called when asynchronous
            # events such as Bluetooth notifications occur.
            self.withDelegate(DeviceDelegate(self))

            # Connecting.
            self._update_device_status(DeviceStatus.CONNECTING)
            self.add_external_features(user_defined_features)
            with lock(self):
                super(Device, self).connect(self.get_mac_address(), self._scan_entry.addrType)

            # Setting MTU size.
            if self.get_type() != DeviceType.PROTEUS:
                time.sleep(self.DELAY_CONNECT_SET_MTU_s)
                self._mtu_bytes = self.setMTU(STL2TransportProtocol.MAXIMUM_ST_MTU_SIZE_bytes)['mtu'][0]
                self._mtu_bytes = self._mtu_bytes - (self._mtu_bytes % STL2TransportProtocol.STM32L4_MINIMUM_BURST_SIZE_bytes)
                logging.getLogger('BlueST').debug("MTU size: {}".format(self._mtu_bytes))

            # Getting services.
            with lock(self):
                services = self.getServices()
            if not services:
                self.disconnect()
                return False

            # Handling Debug, Config, and Feature characteristics.
            for service in services:
                if Debug.is_debug_service(str(service.uuid)):
                    # Handling Debug.
                    self._debug_console = self._build_debug_console(service)
                #elif Config.is_config_service(str(service.uuid)):
                    # Handling Config.
                    #pass

                # Getting characteristics.
                with lock(self):
                    characteristics = service.getCharacteristics()

                for characteristic in characteristics:
                    # Printing characteristic implemented by the device.
                    logging.getLogger('BlueST').debug('Characteristic implemented: {} | {} | {}'.format(
                        characteristic.uuid,
                        characteristic.propertiesToString(),
                        characteristic.getHandle()))

                    # Storing characteristics' handle to characteristic mapping.
                    with lock(self):
                        self._char_handle_to_characteristic_dict[
                            characteristic.getHandle()] = characteristic
                        if characteristic.uuid == Config.CONFIG_COMMAND_BLUESTSDK_FEATURE_UUID:
                            self._command_characteristic = characteristic

                    # Building base features declared by the characteristic.
                    if FeatureCharacteristic.declares_base_features(str(characteristic.uuid)):
                        self._build_base_features_upon_connection(characteristic)

                    # Building extended features declared by the characteristic.
                    elif FeatureCharacteristic.declares_extended_features(str(characteristic.uuid)):
                        self._build_extended_features_upon_connection(
                            characteristic,
                            [FeatureCharacteristic.get_extended_feature_class(characteristic.uuid)])

                    # Building external features declared by the characteristic.
                    elif bool(self._external_uuid_to_features_dict) \
                        and characteristic.uuid in self._external_uuid_to_features_dict:
                        self._build_external_features_upon_connection(
                            characteristic,
                            [self._external_uuid_to_features_dict[characteristic.uuid]])

            # For each feature store a reference to the characteristic offering the
            # feature, useful to enable/disable notifications on the characteristic
            # itself.
            self._set_features_characteristics()

            # Change device's status.
            self._update_device_status(DeviceStatus.CONNECTED)

            return self._status == DeviceStatus.CONNECTED
        except BTLEException as e:
            self._unexpected_disconnect()

    def disconnect(self):
        """Close the connection to the device.

        Returns:
            bool: True if the disconnection to the device has been successful,
            False otherwise.
        """
        try:
            if not self.is_connected():
            #    logging.getLogger('BlueST').info("---------------------> Disconnected")
                return False
            #logging.getLogger('BlueST').info("---------------------> Connected")

            # Disconnecting.
            self._update_device_status(DeviceStatus.DISCONNECTING)
            with lock(self):
                super(Device, self).disconnect()
            self._update_device_status(DeviceStatus.IDLE)

            return self._status == DeviceStatus.IDLE
        except BTLEException as e:
            self._unexpected_disconnect()

    def add_external_features(self, user_defined_features):
        """Add features to an already discovered device.

        This method has effect only if called before connecting to the device.
        If a UUID is already known, it will be overwritten with the new list of
        features.

        Example:
        # Adding a 'FeatureHeartRate' feature to a Nucleo device and mapping
        # it to the standard '00002a37-0000-1000-8000-00805f9b34fb' Heart Rate
        # Measurement characteristic.
        map = UUIDToFeatureMap()
        map.put(uuid.UUID('00002a37-0000-1000-8000-00805f9b34fb'),
            feature_heart_rate.FeatureHeartRate)
        device.add_external_features(map)
        # Connecting to the device.
        device.connect()

        Otherwise, it is possible to add features before performing
        the discovery process (see 
        :meth:`blue_st_sdk.manager.Manager.addFeaturesToDevice()` method).

        Args:
            user_defined_features (dict): User-defined features to be added.
        """
        if user_defined_features:
            self._external_uuid_to_features_dict.put_all(user_defined_features)

    def get_mac_address(self):
        """Get the MAC address of the device.

        Returns:
            str: The MAC address of the device (hexadecimal string separated by
            colons).
        """
        try:
            return self._scan_entry.addr
        except BTLEException as e:
            self._unexpected_disconnect()

    def get_status(self):
        """Get the status of the device.

        Returns:
            :class:`blue_st_sdk.device.DeviceStatus`: The status of the device.
        """
        return self._status

    def get_name(self):
        """Get the name of the device.

        Returns:
            str: The name of the device.
        """
        return self._advertising_data.get_name()

    def get_friendly_name(self):
        """Get a friendly name of the device.

        Returns:
            str: A friendly name of the device.
        """
        if not self._friendly_name:
            mac_address = self.get_mac_address()
            if mac_address is not None and len(mac_address) > 0:
                mac_address_clean = mac_address.replace(":", "")
            self._friendly_name = self.get_name()\
                + " @"\
                + mac_address_clean.substring(
                    len(mac_address_clean) - min(6, mac_address_clean.length()),
                    len(mac_address_clean)
                )
        return self._friendly_name

    def get_type(self):
        """Get the type of the device.

        Returns:
            :class:`blue_st_sdk.device.DeviceType`: The type of the device.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidAdvertisingDataException`
            if the device type is unknown.
        """
        return self._advertising_data.get_device_type()

    def get_type_id(self):
        """Get the type identifier of the device.

        Returns:
            int: The type identifier of the device.
        """
        return self._advertising_data.get_device_id()

    def get_protocol_version(self):
        """Get the device protocol version.

        Returns:
            int: The version of the BlueST protocol implemented by the device.
        """
        return self._advertising_data.get_protocol_version()

    def get_features(self, feature_class=None):
        """Get the list of features, either the declared-in-advertisement-data
        or the implemented, depending on whether the device is respectively
        non-connected or connected.

        If a certain feature class is given, get the list of features of the
        specific type (class name) among those implemented.

        Args:
            feature_class (class, optional): Type (class name) of the feature to
            search for.

        Returns:
            list: A list of features. An empty list if no features are found.
        """
        if not self.is_connected():
            features = self._declared_features
        elif not feature_class:
            features = self._implemented_features
        else:
            features = []
            for feature in self._implemented_features:
                if isinstance(feature, feature_class):
                    features.append(feature)
        return features

    def get_feature(self, feature_class):
        """Get a feature of the given type (class name).

        Args:
            feature_class (class): Type (class name) of the feature to search
            for.

        Returns:
            The feature of the given type (class name) if declared by this device,
            "None" otherwise.
        """
        features = self.get_features(feature_class)
        if len(features) != 0:
            return features[0]
        return None

    def get_tx_power(self):
        """Get the device transmission power.

        Returns:
            int: The device transmission power.
        """
        return self._advertising_data.get_tx_power()

    def get_rssi(self):
        """Get the last known value of the RSSI.

        Returns:
            int: The last known value of the RSSI in db.
        """
        return self._rssi

    def get_last_rssi_update_date(self):
        """Get the time of the last RSSI update received.

        Returns:
            datetime: The time of the last RSSI update received. Refer to
            `datetime <https://docs.python.org/3/library/datetime.html>`_
            for more information.
        """
        return self._last_rssi_update

    def is_connectable(self):
        """Checking whether the device accepts direct connections.
        
        Returns:
            bool: True if the device accepts direct connections,
            False otherwise.
        """
        return self._connectable

    def get_mtu_bytes(self):
        """Get the MTU size in bytes.
        
        Returns:
            int: The MTU size in bytes.
        """
        return self._mtu_bytes

    def get_advertising_data(self):
        """Update advertising data.

        Returns:
            :class:`blue_st_sdk.advertising_data.blue_st_advertising_data.BlueSTAdvertisingData`:
            Formatted Blue ST Advertising Data object.
        """
        return self._advertising_data

    def update_advertising_data(self, ble_advertising_data):
        """Update advertising data.

        Args:
            ble_advertising_data (list): BLE advertising data,
            as scanned by the bluepy library. Refer to 'getScanData()'
            method of
            `ScanEntry <https://ianharvey.github.io/bluepy-doc/scanentry.html>`_
            class for more information.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidAdvertisingDataException`
            is raised if the advertising data is not well formed.
        """
        try:
            self._advertising_data = BlueSTAdvertisingDataParser.parse(
                ble_advertising_data)
        except BlueSTInvalidAdvertisingDataException as e:
            raise e

    def update_rssi(self, rssi):
        """Update the RSSI value.

        To be called whenever the :class:`blue_st_sdk.manager.Manager` class
        receives a new advertising data from this device.

        Args:
            rssi (int): New RSSI value.
        """
        self._rssi = rssi
        self._last_rssi_update = datetime.now()
        #if self._status == DeviceStatus.LOST:
        #    self._update_device_status(DeviceStatus.IDLE)

    def is_connected(self):
        """Check whether the device is connected.

        Returns:
            bool: True if the device is connected, False otherwise.
        """
        return self._status == DeviceStatus.CONNECTED

    def is_sleeping(self):
        """Check whether the device is sleeping.

        Returns:
            bool: True if the device is sleeping, False otherwise.
        """
        return self._advertising_data.is_board_sleeping()

    def equals(self, device):
        """Compare the current device with the given one.

        Returns:
            bool: True if the current device is equal to the given device, False
            otherwise.
        """
        return isinstance(device, Device)\
               and (device == self or self.get_mac_address() == device.get_mac_address())

    def characteristic_can_be_read(self, characteristic):
        """Check if a characteristics can be read.

        Args:
            characteristic (Characteristic): The BLE characteristic to check.
            Refer to
            `Characteristic <https://ianharvey.github.io/bluepy-doc/characteristic.html>`_
            for more information.

        Returns:
            :class:`blue_st_sdk.device.CharacteristicProperty`: Property of the
            characteristic.
        """
        try:
            if characteristic:
                with lock(self):
                    if "READ" in characteristic.propertiesToString():
                        return CharacteristicProperty.READ
            return CharacteristicProperty.NOPE
        except BTLEException as e:
            self._unexpected_disconnect()

    def characteristic_can_be_written(self, characteristic):
        """Check if a characteristics can be written.

        Args:
            characteristic (Characteristic): The BLE characteristic to check.
            Refer to
            `Characteristic <https://ianharvey.github.io/bluepy-doc/characteristic.html>`_
            for more information.

        Returns:
            :class:`blue_st_sdk.device.CharacteristicProperty`: Property of the
            characteristic.
        """
        try:
            if characteristic:
                with lock(self):
                    if "WRITE NO RESPONSE" in characteristic.propertiesToString():
                        return CharacteristicProperty.WRITE_NO_RESPONSE
                    if "WRITE" in characteristic.propertiesToString():
                        return CharacteristicProperty.WRITE
            return CharacteristicProperty.NOPE
        except BTLEException as e:
            self._unexpected_disconnect()

    def characteristic_can_be_notified(self, characteristic):
        """Check if a characteristics can be notified.

        Args:
            characteristic (Characteristic): The BLE characteristic to check.
            Refer to
            `Characteristic <https://ianharvey.github.io/bluepy-doc/characteristic.html>`_
            for more information.

        Returns:
            :class:`blue_st_sdk.device.CharacteristicProperty`: Property of the
            characteristic.
        """
        try:
            if characteristic:
                with lock(self):
                    if "NOTIFY" in characteristic.propertiesToString():
                        return CharacteristicProperty.NOTIFY
            return CharacteristicProperty.NOPE
        except BTLEException as e:
            self._unexpected_disconnect()

    def read_feature(self, feature):
        """Request to read a feature.

        Args:
            feature (:class:`blue_st_sdk.feature.Feature`): The feature to read.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
            is raised if the feature is not enabled or the operation
            required is not supported.
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidDataException`
            if the data array has not enough data to read.
        """
        if not feature.is_enabled():
            raise BlueSTInvalidOperationException(
                'The "' + feature.get_name() + '" feature is not enabled.')

        characteristic = feature.get_characteristic()
        if self.characteristic_can_be_read(characteristic) == \
            CharacteristicProperty.NOPE:
            raise BlueSTInvalidOperationException(
                'The "' + feature.get_name() + '" feature is not readable.')

        # Reading data.
        try:
            with lock(self):
                char_handle = characteristic.getHandle()
                data = self.readCharacteristic(char_handle)

            # Calling on-read callback.
            if self._debug_console and \
                Debug.is_debug_characteristic(str(characteristic.uuid)):
                # Calling on-read callback for a debug characteristic.
                self._debug_console.on_update_characteristic(
                    characteristic, data)
            else:
                # Calling on-read callback for the other characteristics.
                self._update_features(char_handle, data, notify_update=False)
        except BlueSTInvalidDataException as e:
            raise e
        except BTLEException as e:
            self._unexpected_disconnect()

    def write_feature(self, feature, data):
        """Request to write a feature.

        Args:
            feature (:class:`blue_st_sdk.feature.Feature`): The feature to
            write.
            data (str): The data to be written.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
            is raised if the feature is not enabled or the operation
            required is not supported.
        """
        if not feature.is_enabled():
            raise BlueSTInvalidOperationException(
                'The "' + feature.get_name() + '" feature is not enabled.')

        characteristic = feature.get_characteristic()
        characteristic_write_property = \
            self.characteristic_can_be_written(characteristic)
        if characteristic_write_property == CharacteristicProperty.NOPE:
            raise BlueSTInvalidOperationException(
                'The "' + feature.get_name() + '" feature is not writable.')

        try:
            with lock(self):
                char_handle = characteristic.getHandle()
                self.writeCharacteristic(
                    char_handle,
                    data,
                    True if characteristic_write_property == CharacteristicProperty.WRITE else False)
        except BTLEException as e:
            self._unexpected_disconnect()

    def send_command(self, data):
        """Send a command.

        Args:
            data (str): The data to be written.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
            is raised if the feature is not enabled or the operation
            required is not supported.
        """        
        characteristic = self._command_characteristic
        characteristic_write_property = \
            self.characteristic_can_be_written(characteristic)
        if characteristic_write_property == CharacteristicProperty.NOPE:
            raise BlueSTInvalidOperationException(
                'The "' + characteristic.uuid + '" characteristic is not writable.')

        try:
            with lock(self):
                char_handle = characteristic.getHandle()
                self.writeCharacteristic(
                    char_handle,
                    data,
                    True if characteristic_write_property == CharacteristicProperty.WRITE else False)
        except BTLEException as e:
            self._unexpected_disconnect()

    def set_notification_status(self, characteristic, status):
        """Ask the device to set the notification status of the given
        characteristic.

        Args:
            characteristic (Characteristic): The BLE characteristic to check.
            Refer to
            `Characteristic <https://ianharvey.github.io/bluepy-doc/characteristic.html>`_
            for more information.
            status (bool): True if the notifications have to be turned on, False
            otherwise.
        """
        try:
            with lock(self):
                self.writeCharacteristic(characteristic.getHandle() + 1,
                    self._NOTIFICATION_ON if status else self._NOTIFICATION_OFF, True)
        except BTLEException as e:
            self._unexpected_disconnect()

    def enable_notifications(self, feature):
        """Ask the device to notify when a feature updates its value.

        The received values are notified thought a feature listener.

        Args:
            feature (:class:`blue_st_sdk.feature.Feature`): The given feature.

        Returns:
            bool: False if the feature is not handled by this device, or it is
            disabled, or it is not possible to turn notifications on for it,
            True otherwise.
        """
        if not feature.is_enabled() or feature.get_parent_device() != self:
            return False
        characteristic = feature.get_characteristic()
        if self.characteristic_can_be_notified(characteristic) == \
            CharacteristicProperty.NOTIFY:
            feature.set_notify(True)
            self.set_notification_status(characteristic, True)
            return True
        return False

    def disable_notifications(self, feature):
        """Ask the device to stop notifying when a feature updates its value.

        Args:
            feature (:class:`blue_st_sdk.feature.Feature`): The given feature.

        Returns:
            bool: False if the feature is not handled by this device, or it is
            disabled, or it is not possible to turn notifications off for it,
            True otherwise.
        """
        if not feature.is_enabled() or feature.get_parent_device() != self:
            return False
        characteristic = feature.get_characteristic()
        if self.characteristic_can_be_notified(characteristic) == \
            CharacteristicProperty.NOTIFY:
            feature.set_notify(False)
            if not self.characteristic_has_other_notifying_features(
                    characteristic, feature):
                self.set_notification_status(characteristic, False)
            return True
        return False

    def notifications_enabled(self, feature):
        """Check whether notifications are enabled for a feature.

        Args:
            feature (:class:`blue_st_sdk.feature.Feature`): The given feature.

        Returns:
            bool: True if notifications are enabled, False otherwise.
        """
        return feature.is_notifying()

    def wait_for_notifications(self, timeout_s):
        """Block until a notification is received from the peripheral, or until
        the given timeout has elapsed.

        If a notification is received, the
        :meth:`blue_st_sdk.feature.FeatureListener.on_update` method of any
        added listener is called.

        Args:
            timeout_s (float): Time in seconds to wait before returning.

        Returns:
            bool: True if a notification is received before the timeout elapses,
            False otherwise.
        """
        try:
            if self.is_connected():
                with lock(self):
                    return self.waitForNotifications(timeout_s)
            return False
        except BTLEException as e:
            self._unexpected_disconnect()

    def characteristic_has_other_notifying_features(self, characteristic, feature):
        """Check whether a characteristic has other enabled features beyond the
        given one.

        Args:
            characteristic (Characteristic): The BLE characteristic to check.
            Refer to
            `Characteristic <https://ianharvey.github.io/bluepy-doc/characteristic.html>`_
            for more information.
            feature (:class:`blue_st_sdk.feature.Feature`): The given feature.

        Returns:
            True if the characteristic has other enabled features beyond the
            given one, False otherwise.
        """
        with lock(self):
            features = self._get_corresponding_features(
                characteristic.getHandle())
        for feature_entry in features:
            if feature_entry == feature:
                pass
            elif feature_entry.is_notifying():
                return True
        return False

    def add_listener(self, listener):
        """Add a listener.
        
        Args:
            listener (:class:`blue_st_sdk.device.DeviceListener`): Listener to
            be added.
        """
        if listener:
            with lock(self):
                if not listener in self._listeners:
                    self._listeners.append(listener)

    def remove_listener(self, listener):
        """Remove a listener.

        Args:
            listener (:class:`blue_st_sdk.device.DeviceListener`): Listener to
            be removed.
        """
        if listener:
            with lock(self):
                if listener in self._listeners:
                    self._listeners.remove(listener)

    def remove_listeners(self):
        """Remove all listeners."""
        if self._listeners:
            with lock(self):
                for listener in self._listeners:
                    self._listeners.remove(listener)

    def get_debug(self):
        """Getting a debug console used to read/write debug messages from/to the
        Bluetooth device.

        Returns:
            :class:`blue_st_sdk.debug_console.DebugConsole`: A debug console
            used to read/write debug messages from/to the Bluetooth device.
            None if the device doesn't export the debug service.
        """
        return self._debug_console


class DeviceDelegate(DefaultDelegate):
    """Delegate class for handling Bluetooth Low Energy devices' notifications."""

    def __init__(self, device):
        """Constructor.

        Args:
            device (:class:`blue_st_sdk.device.Device`): The device which sends
            notifications.
        """
        DefaultDelegate.__init__(self)

        self._device = device

    def handleNotification(self, char_handle, data):
        """It is called whenever a notification arises.

        Args:
            char_handle (int): The characteristic's handle to look for.
            data (str): The data notified from the given characteristic.
        """
        try:
            # Calling on-read callback.
            if self._device._debug_console:
                # Calling on-update callback for a debug characteristic.
                characteristic = \
                    self._device._char_handle_to_characteristic_dict[char_handle]
                if Debug.is_debug_characteristic(str(characteristic.uuid)):
                    self._device._debug_console.on_update_characteristic(
                        characteristic, data)
                    return

            # Calling on-read callback for the other characteristics.
            self._device._update_features(char_handle, data, notify_update=True)
        except BlueSTInvalidDataException as e:
            logging.getLogger('BlueST').warning('Error: {}'.format(str(e)))
        except BTLEException as e:
            self._unexpected_disconnect()


class DeviceType(Enum):
    """Type of device."""

    GENERIC = 0x00
    """Unknown device type."""

    STEVAL_WESU1 = 0x01
    """STEVAL-WESU1."""

    STEVAL_STLKT01v1 = 0x02
    """SensorTile."""

    STEVAL_BCNKT01v1 = 0x03
    """BlueCoin."""

    STEVAL_IDB008VX = 0x04
    """BlueNRG2 STEVAL."""

    STEVAL_BCN002v1B = 0x05
    """BlueTile STEVAL."""
    
    STEVAL_MKSBOX1v1 = 0x06
    """SensorTile.box."""

    B_L475E_IOT01A = 0x07
    """Discovery Kit IoT Device."""

    STEVAL_STWINKT1 = 0x08
    """STWIN SensorTile Wireless Industrial Device (L4)."""

    STEVAL_STWINKT1B = 0x09
    """STWIN SensorTile Wireless Industrial Device (L4) with STSAFE."""

    B_L4S5I_IOT01A = 0x0A
    """Discovery Kit IoT Device 1.5."""

    B_U585I_IOT02A = 0x0B
    """Discovery Kit IoT Device 2 (U5)."""

    STEVAL_ASTRA1B = 0x0C
    """Astra (WB + WL)."""

    STEVAL_MKBOXPRO = 0x0D
    """SensorTile.box PRO (U5)."""

    STEVAL_STWINBX1 = 0x0E
    """STWIN.box SensorTile Wireless Industrial Device (U5)."""

    PROTEUS = 0x0F
    """Proteus (WB)."""

    STDES_CBMLORABLE = 0x10
    """STDES-CBMLoRaBLE."""

    STEVAL_MKBOXPRO_B = 0x11
    """SensorTile.box PRO B (U5)."""

    STEVAL_STWINBX1_B = 0x12
    """STWIN.box SensorTile Wireless Industrial Device B (U5)."""

    NUCLEO_F401RE = 0x7F
    """Specific NUCLEO board."""

    NUCLEO_L476RG = 0x7E
    """Specific NUCLEO board."""

    NUCLEO_L053R8 = 0x7D
    """Specific NUCLEO board."""

    NUCLEO_F446RE = 0x7C
    """Specific NUCLEO board."""

    NUCLEO = 0x80
    """NUCLEO board with expansion stack."""

    WB55_NUCLEO = 0x81
    """WB-based board."""

    WB5M_DISCOVERY = 0x82
    """WB-based board."""

    WB55_USB_DONGLE = 0x83
    """WB-based board."""

    WB15_NUCLEO = 0x84
    """WB-based board."""

    WB1M_DISCOVERY = 0x85
    """WB-based board."""

    WBA5X_NUCLEO = 0x8B
    """WB-based board."""

    WBA_DISCOVERY = 0x8C
    """WB-based board."""

    WB09KE_NUCLEO = 0x8D
    """WB-based board."""

    #0x90..0xFF Reserved for custom boards.


class DeviceStatus(Enum):
    """Status of the device."""

    INIT = 'INIT'
    """Dummy initial status."""

    IDLE = 'IDLE'
    """Waiting for a connection and sending advertising data."""

    CONNECTING = 'CONNECTING'
    """Opening a connection with the device."""

    CONNECTED = 'CONNECTED'
    """Connected to the device.
    This status can be fired 2 times while doing a secure connection using
    Bluetooth pairing."""

    DISCONNECTING = 'DISCONNECTING'
    """Closing the connection to the device."""

    LOST = 'LOST'
    """The advertising data has been received for some time, but not anymore."""

    UNREACHABLE = 'UNREACHABLE'
    """The device disappeared without first disconnecting."""

    DEAD = 'DEAD'
    """Dummy final status."""


class CharacteristicProperty(Enum):
    """Properties of a characteristic."""

    NOPE = 0
    """Nope."""

    READ = 1
    """Read."""

    NOTIFY = 2
    """Notify."""

    WRITE_NO_RESPONSE = 3
    """Write without response."""

    WRITE = 4
    """Write with response."""


# INTERFACES

class DeviceListener(object):
    """Interface used by the :class:`blue_st_sdk.device.Device` class to notify
    changes of a device's status.
    """
    __metaclass__ = ABCMeta

    # @abstractmethod
    # def on_status_change(self, device, new_status, old_status):
    #     """To be called whenever a device changes its status.

    #     Args:
    #         device (:class:`blue_st_sdk.device.Device`): Device that has changed its
    #         status.
    #         new_status (:class:`blue_st_sdk.device.DeviceStatus`): New status.
    #         old_status (:class:`blue_st_sdk.device.DeviceStatus`): Old status.

    #     Raises:
    #         :exc:`NotImplementedError` if the method has not been implemented.
    #     """
    #     raise NotImplementedError('You must implement "on_status_change()" to '
    #                               'use the "DeviceListener" class.')

    @abstractmethod
    def on_connect(self, device):
        """To be called whenever a device connects to a host.

        Args:
            device (:class:`blue_st_sdk.device.Device`): Device that has connected to a
            host.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError('You must implement "on_connect()" to '
                                  'use the "DeviceListener" class.')

    @abstractmethod
    def on_disconnect(self, device, unexpected=False):
        """To be called whenever a device disconnects from a host.

        Args:
            device (:class:`blue_st_sdk.device.Device`): Device that has disconnected
            from a host.
            unexpected (bool, optional): True if the disconnection is unexpected,
            False otherwise (called by the user).

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError('You must implement "on_disconnect()" to '
                                  'use the "DeviceListener" class.')
