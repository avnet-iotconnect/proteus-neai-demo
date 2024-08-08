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


"""manager

The manager module is responsible for managing the discovery process of
Bluetooth Low Energy (BLE) devices and allocating the needed resources.
"""


# IMPORT

from abc import ABCMeta
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor
from bluepy.btle import Scanner
from bluepy.btle import DefaultDelegate
from bluepy.btle import BTLEException
import logging
import threading

import blue_st_sdk.utils.globals
from blue_st_sdk.device import Device
from blue_st_sdk.utils.ble_device_definitions import FeatureCharacteristic
from blue_st_sdk.utils.blue_st_exceptions import BlueSTInvalidFeatureBitMaskException
from blue_st_sdk.utils.blue_st_exceptions import BlueSTInvalidAdvertisingDataException
from blue_st_sdk.utils.blue_st_exceptions import BlueSTInvalidOperationException
from blue_st_sdk.utils.python_utils import lock
from blue_st_sdk.utils.python_utils import lock_for_object
from blue_st_sdk import blue_st_sdk_le


# CLASSES


class _ScannerDelegate(DefaultDelegate):
    """Delegate class to scan Bluetooth Low Energy devices."""

    _SCANNING_TIME_PROCESS_s = 1
    """Default Bluetooth scanning timeout in seconds for a single call to
    bluepy's process() method."""

    def __init__(self, show_non_bluest_devices=False):
        """Constructor.

        Args:
            show_non_bluest_devices (bool, optional): If True shows also non-BlueST
            devices, if any, i.e. devices that do not comply with the BlueST protocol
            advertising data format, nothing otherwise.
        """
        DefaultDelegate.__init__(self)

        # Handling warnings.
        self._show_non_bluest_devices = show_non_bluest_devices

        # Creating Bluetooth Manager.
        self._manager = Manager.instance()

    def handleDiscovery(self, scan_entry, is_new_device, is_new_data):
        """Discovery handling callback.

        Called when an advertising data is received from a BLE device while a
        Scanner object is active.

        Args:
            scan_entry (ScanEntry): BLE device. It contains device information
            and advertising data. Refer to
            `ScanEntry <https://ianharvey.github.io/bluepy-doc/scanentry.html>`_
            for more information.
            is_new_device (bool): True if the device (as identified by its MAC
            address) has not been seen before by the scanner, False
            otherwise.
            is_new_data (bool): True if new or updated advertising data is
            available.
        """
        try:
            #logging.getLogger('BlueST').info("MAC: {}/tis_new_device: {}/tis_new_data: {}".format(
            #    scan_entry.addr, is_new_device, is_new_data))
            device = None
            if is_new_device:
                #logging.getLogger('BlueST').info("New device %s" % (scan_entry.addr))
                device = Device(scan_entry, self._manager)
                device.build()
                """Alternative to the snippet below (TBC)."""
                # Add a device to the list of discovered devices
                # and notify the listeners, if any.
                self._manager._add_device(device)
                self._manager._notify_device_discovered(device)
                """
                # Check whether the device has already been added to the list of
                # discovered devices.
                with lock_for_object(self._manager._discovered_devices_dict):
                    old_device = self._manager.get_device_with_mac_address(
                        device.get_mac_address())
                    if old_device is None:
                        # Add a device to the list of discovered devices
                        # and notify the listeners, if any.
                        self._manager._add_device(device)
                        self._manager._notify_device_discovered(device)
                    else:
                        # Update its advertising data in case it has already
                        # been discovered previously.
                        old_device.update_rssi(device.get_rssi())
                        old_device.update_advertising_data(device.get_advertising_data())
                """
            elif is_new_data:
                #logging.getLogger('BlueST').info("Updated data from %s" % (scan_entry.addr))
                devices = self._manager._get_devices_dictionary()
                if scan_entry.addr in devices:
                    device = devices[scan_entry.addr]
                    device.update_rssi(scan_entry.rssi)
                    device.update_advertising_data(scan_entry.getScanData())
                    self._manager._notify_advertising_data_update(
                        device,
                        device.get_advertising_data()
                    )
            else:
                #logging.getLogger('BlueST').info("Unchanged data from %s" % (scan_entry.addr))
                devices = self._manager._get_devices_dictionary()
                if scan_entry.addr in devices:
                    device = devices[scan_entry.addr]
                    device.update_rssi(scan_entry.rssi)
                    device.update_advertising_data(scan_entry.getScanData())
                    self._manager._notify_advertising_data_unchanged(
                        device,
                        device.get_advertising_data()
                    )

        except (BlueSTInvalidAdvertisingDataException,
                BlueSTInvalidOperationException,
                BTLEException) as e:
            if self._show_non_bluest_devices:
                self._manager._notify_device_discovered(device, str(e))


class _StoppableScanner(threading.Thread):
    """Scanner class which can be started and stopped asynchronously.

    Non-thread-safe.

    It is implemented as a thread which checks regularly for the stop
    condition within the :meth:`run()` method; it can be stopped by calling the
    :meth:`stop()` method.
    """

    def __init__(self, passive_scan=False, show_non_bluest_devices=False, *args, **kwargs):
        """Constructor.

        Args:
            passive_scan (bool, optional): If True the bluetooth stack performs
            a passive scan, so that it just listens to advertising frames
            (ADV_IND); otherwise, it performs an active scan, so that it
            requests additional frames (ADV_RSP) for each advertising frame
            received (ADV_IND).
            show_non_bluest_devices (bool, optional): If True shows also non-BlueST
            devices, if any, i.e. devices that do not comply with the BlueST protocol
            advertising data format, nothing otherwise.
        """
        try:
            super(_StoppableScanner, self).__init__(*args, **kwargs)
            self._passive_scan = passive_scan
            self._stop_called = threading.Event()
            self._process_done = threading.Event()
            with lock(self):
                self._scanner = Scanner().withDelegate(_ScannerDelegate(show_non_bluest_devices))
        except BTLEException as e:
            # Save details of the exception raised but don't re-raise, just
            # complete the function.
            import sys
            self._exc = sys.exc_info()

    def run(self):
        """Run the thread."""
        self._stop_called.clear()
        self._process_done.clear()
        try:
            with lock(self):
                self._scanner.clear()
                self._exc = None
                self._scanner.start(passive=self._passive_scan)
                while True:
                    # logging.getLogger('BlueST').info('.')
                    self._scanner.process(_ScannerDelegate._SCANNING_TIME_PROCESS_s)
                    if self._stop_called.isSet():
                        self._process_done.set()
                        break

        except BTLEException as e:
            # Save details of the exception raised but don't re-raise, just
            # complete the function.
            import sys
            self._exc = sys.exc_info()

    def stop(self):
        """Stop the thread."""
        self._stop_called.set()
        while not (self._process_done.isSet() or self._exc):
            pass
        try:
            self._exc = None
            with lock(self):
                self._scanner.stop()
        except BTLEException as e:
            # Save details of the exception raised but don't re-raise, just
            # complete the function.
            import sys
            self._exc = sys.exc_info()

    def join(self):
        """Join the thread.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
            is raised if this method is not run as root.
        """
        super(_StoppableScanner, self).join()
        if self._exc:
            msg = ('\nBluetooth error: {}'.format(self._exc))
            raise BlueSTInvalidOperationException(msg)


class Manager(object):
    """Singleton class to manage the discovery of Bluetooth Low Energy (BLE)
    devices.

    Before starting the scanning process, it is possible to define a new Device
    Id and to register/add new features to already defined devices.

    It notifies a new discovered device through the
    :class:`blue_st_sdk.manager.ManagerListener` class.
    Each callback is performed asynchronously by a thread running in background.
    """

    SCANNING_TIME_DEFAULT_s = 10
    """Default Bluetooth scanning timeout in seconds."""

    _INSTANCE = None
    """Instance object."""

    _NUMBER_OF_THREADS = 5
    """Number of threads to be used to notify the listeners."""

    _features_decoder_dict  = {}
    """Features decoder dictionary.
    Dictionary that maps device identifiers to dictionaries that map
    feature-masks to feature-classes.
    """

    def __init__(self):
        """Constructor.

        Raises:
            :exc:`Exception` is raised in case an instance of the same class has
            already been instantiated.
        """
        # Raise an exception if an instance has already been instantiated.
        if self._INSTANCE:
            msg = '\nAn instance of "Manager" class already exists.'
            raise BlueSTInvalidOperationException(msg)

        self._scanner = None
        """BLE scanner."""

        self._is_discovering = False
        """Scanning status."""

        self._discovered_devices_dict = dict()
        """List of discovered devices."""

        try:
            self._bluestsdkle = blue_st_sdk_le.BlueSTSDKLE()
            """SDK object to handle BlueST LE protocol."""
        except Exception as e:
            logging.getLogger('BlueST').info(str(e))
            #raise e

        self._scanner_thread = None
        """Stoppable-scanner object."""

        self._thread_pool = ThreadPoolExecutor(Manager._NUMBER_OF_THREADS)
        """Pool of thread used to notify the listeners."""

        self._listeners = []
        """List of listeners to the manager changes.
        It is a thread safe list, so a listener can subscribe itself through a
        callback."""

    @classmethod
    def instance(self):
        """Get an instance of the class.

        Returns:
            :class:`blue_st_sdk.manager.Manager`: An instance of the class.
        """
        if self._INSTANCE is None:
            self._INSTANCE = Manager()
        return self._INSTANCE

    def discover(
        self,
        timeout_s=SCANNING_TIME_DEFAULT_s,
        passive_scan=False,
        asynchronous=False,
        show_non_bluest_devices=False
    ):
        """Perform the discovery process.

        This method can be run in synchronous (blocking) or asynchronous
        (non-blocking) way. Default is synchronous.

        The discovery process will last *timeout_s* seconds if provided, a
        default timeout otherwise.

        Please note that when running a discovery process, the already connected
        devices get disconnected (limitation intrinsic to the bluepy library).

        Args:
            timeout_s (int, optional): Time in seconds to wait before stopping
            the discovery process.
            passive_scan (bool, optional): If True the bluetooth stack performs
            a passive scan, so that it just listens to advertising frames
            (ADV_IND); otherwise, it performs an active scan, so that it
            requests additional frames (ADV_RSP) for each advertising frame
            received (ADV_IND).
            asynchronous (bool, optional): If True the method is run in
            asynchronous way, thus non-blocking the execution of the thread,
            the opposite otherwise.
            show_non_bluest_devices (bool, optional): If True shows also non-BlueST
            devices, if any, i.e. devices that do not comply with the BlueST protocol
            advertising data format, nothing otherwise.

        Returns:
            bool: True if the synchronous discovery has finished or if the
            asynchronous discovery has started, False if a discovery is already
            running.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
            is raised if this method is not run as root.
        """
        try:
            if not asynchronous:
                # Synchronous version.
                if self.is_discovering():
                    return False
                self._discovered_devices_dict = dict()
                self._notify_discovery_change(True)
                with lock(self):
                    self._scanner = Scanner().withDelegate(
                        _ScannerDelegate(show_non_bluest_devices)
                    )
                    self._scanner.scan(timeout_s, passive_scan)
                self._notify_discovery_change(False)
                return True
            else:
                # Asynchronous version.
                if not self.start_discovery(passive_scan, show_non_bluest_devices):
                    return False
                threading.Timer(timeout_s, self.stop_discovery).start()
                return True
        except Exception as e:
            msg = ('\nBluetooth error: {}'.format(e))
            raise BlueSTInvalidOperationException(msg)

    def start_discovery(
        self,
        passive_scan=False,
        show_non_bluest_devices=False
    ):
        """Start the discovery process.

        This is an asynchronous (non-blocking) method.

        The discovery process will last indefinitely, until stopped by a call to
        :meth:`stop_discovery()`.
        This method can be particularly useful when starting a discovery process
        from an interactive GUI.

        Please note that when running a discovery process, the already connected
        devices get disconnected (limitation intrinsic to the bluepy library).

        Args:
            passive_scan (bool, optional): If True the bluetooth stack performs
            a passive scan, so that it just listens to advertising frames
            (ADV_IND); otherwise, it performs an active scan, so that it
            requests additional frames (ADV_RSP) for each advertising frame
            received (ADV_IND).
            show_non_bluest_devices (bool, optional): If True shows also non-BlueST
            devices, if any, i.e. devices that do not comply with the BlueST protocol
            advertising data format, nothing otherwise.

        Returns:
            bool: True if the discovery has started, False if a discovery is
            already running.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
            is raised if this method is not run as root.
        """
        try:
            # logging.getLogger('BlueST').info('start_discovery()')
            if self.is_discovering():
                return False
            self._discovered_devices_dict = dict()
            self._notify_discovery_change(True)
            self._scanner_thread = _StoppableScanner(passive_scan, show_non_bluest_devices)
            self._scanner_thread.start()
            return True
        except BTLEException as e:
            # msg = (
            #     '\nBluetooth scanning requires root privileges, '
            #     'so please run the application with "sudo".'
            # )
            msg = ('\nBluetooth error: {}'.format(e))
            raise BlueSTInvalidOperationException(msg)

    def stop_discovery(self):
        """Stop a discovery process.

        To be preceeded by a call to :meth:`start_discovery()`.
        This method can be particularly useful when stopping a discovery process
        from an interactive GUI.

        Returns:
            bool: True if the discovery has been stopped, False if there are no
            running discovery processes.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
            is raised if this method is not run as root.
        """
        try:
            # logging.getLogger('BlueST').info('stop_discovery()')
            if self.is_discovering():
                self._notify_discovery_change(False)
                self._scanner_thread.stop()
                self._scanner_thread.join()
                return True
            return False
        except BTLEException as e:
            msg = ('\nBluetooth error: {}'.format(e))
            raise BlueSTInvalidOperationException(msg)

    def is_discovering(self):
        """Check the discovery process.

        Returns:
            bool: True if the manager is looking for new devices, False otherwise.
        """
        return self._is_discovering

    def reset_discovery(self):
        """Reset the discovery process.

        Stop the discovery process and remove all the already discovered devices.
        Device already connected to the host will be kept in the list.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
            is raised if this method is not run as root.
        """
        try:
            if self.is_discovering():
                self.stop_discovery()
            self._remove_devices()
        except BTLEException as e:
            msg = ('\nBluetooth error: {}'.format(e))
            raise BlueSTInvalidOperationException(msg)

    def _notify_discovery_change(self, status):
        """Notify :class:`blue_st_sdk.manager.ManagerListener` objects that the
        discovery process has changed status.

        Args:
            status (bool): If True the discovery starts, if False the discovery
            stops.
        """
        self._is_discovering = status
        for listener in self._listeners:
            # Calling user-defined callback.
            self._thread_pool.submit(listener.on_discovery_change(self, status))

    def _notify_device_discovered(self, device, error_message=False):
        """Notify :class:`blue_st_sdk.manager.ManagerListener` objects that a
        new device has been discovered.

        Args:
            device (:class:`blue_st_sdk.device.Device`): Device discovered.
            error_message (str): Error message in case the advertisement data
            is not valid.
        """
        for listener in self._listeners:
            # Calling user-defined callback.
            self._thread_pool.submit(listener.on_device_discovered(self, device, error_message))

    def _notify_advertising_data_update(self, device, advertising_data):
        """Notify :class:`blue_st_sdk.manager.ManagerListener` objects that a
        new advertising data has been collected.

        Args:
            device (:class:`blue_st_sdk.device.Device`): Device whose advertising data
            has updated.
            advertising_data (:class:`blue_st_sdk.advertising_data.blue_st_advertising_data.BlueSTAdvertisingData`):
            BlueST advertising data object.
        """
        for listener in self._listeners:
            # Calling user-defined callback.
            self._thread_pool.submit(
                listener.on_advertising_data_updated(self, device, advertising_data)
            )

    def _notify_advertising_data_unchanged(self, device, advertising_data):
        """Notify :class:`blue_st_sdk.manager.ManagerListener` objects that an
        unchanged advertising data has been collected.

        Args:
            device (:class:`blue_st_sdk.device.Device`): Device whose advertising data
            has not changed.
            advertising_data (:class:`blue_st_sdk.advertising_data.blue_st_advertising_data.BlueSTAdvertisingData`):
            BlueST advertising data object.
        """
        for listener in self._listeners:
            # Calling user-defined callback.
            self._thread_pool.submit(
                listener.on_advertising_data_unchanged(self, device, advertising_data)
            )

    def _add_device(self, device):
        """Add a device to the list of discovered devices.

        Args:
            device (:class:`blue_st_sdk.device.Device`): Device to add.
        """
        with lock_for_object(self._discovered_devices_dict):
            self._discovered_devices_dict[device.get_mac_address()] = device
        #logging.getLogger('BlueST').info("Added. Dict size = %d." % (len(self._manager._get_devices_dictionary())))

    def _remove_devices(self):
        """Remove all already discovered devices.."""
        with lock_for_object(self._discovered_devices_dict):
            self._discovered_devices_dict = dict()

    def _remove_unconnected_devices(self):
        """Remove all devices not connected to the host."""
        with lock_for_object(self._discovered_devices_dict):
            for mac_address, device in self._discovered_devices_dict.items():
                if not device.is_connected():
                    self._discovered_devices_dict.pop(mac_address, None)

    def _get_devices_dictionary(self):
        """Get the dictionary of the discovered devices until the time of
        invocation.

        Returns:
            dict of :class:`blue_st_sdk.device.Device`: The dictionary of all
            discovered devices until the time of invocation.
        """
        with lock_for_object(self._discovered_devices_dict):
            return self._discovered_devices_dict

    def get_devices(self):
        """Get the list of the discovered devices until the time of invocation.

        Returns:
            list of :class:`blue_st_sdk.device.Device`: The list of all discovered
            devices until the time of invocation.
        """
        with lock_for_object(self._discovered_devices_dict):
            return list(self._discovered_devices_dict.values())

    def get_device_with_mac_address(self, mac_address):
        """Get the device with the given MAC address.

        Args:
            mac_adress (str): Unique string identifier that identifies a device.

        Returns:
            :class:`blue_st_sdk.device.Device`: The device with the given MAC address,
            None if not found.
        """
        with lock_for_object(self._discovered_devices_dict):
            return self._discovered_devices_dict[mac_address] if mac_address in self._discovered_devices_dict else None

    def get_device_with_name(self, name):
        """Get the device with the given name.

        Note:
            As the name is not unique, it will return the fist device matching.
            The match is case sensitive.

        Args:
            name (str): Name of the device.

        Returns:
            :class:`blue_st_sdk.device.Device`: The device with the given name, None
            if not found.
        """
        with lock_for_object(self._discovered_devices_dict):
            for device in list(self._discovered_devices_dict.values()):
                if device.get_name() == name:
                    return device
        return None
    
    def set_bluest_le_catalog(self, catalog_url):
        """Set the catalog URL for the BlueST LE protocol.
        
        Args:
            catalog_url (str): Catalog URL for the BlueST LE protocol.

        Raises:
            :exc:`Exception` is raised in case the catalog is not valid.
        """
        try:
            self._bluestsdkle = blue_st_sdk_le.BlueSTSDKLE(catalog_url)
        except Exception as e:
            raise e

    def decode_bluest_le(self, advertising_data):
        """Decode BlueST LE advertising data.

        Args:
            advertising_data (:class:`blue_st_sdk.advertising_data.blue_st_advertising_data.BlueSTAdvertisingData`):
            BlueST advertising data object.

        Raises:
            :exc:`Exception` is raised in case the advertising data is not valid.
        """
        try:
            message_json = self._bluestsdkle.parse_and_format_message(
                advertising_data.get_device_id(),
                advertising_data.get_firmware_id(),
                advertising_data.get_payload_id(),
                bytes(advertising_data.get_option_bytes())
            )
            return message_json

        except Exception as e:
            logging.getLogger('BlueST').info(
                "Cannot parse raw data, error while reading catalog: {}.".format(str(e))
            )
            logging.getLogger('BlueST').info(
                "device_id: {}, firmware_id: {}, payload_id: {}".format(
                    advertising_data.get_device_id(),
                    advertising_data.get_firmware_id(),
                    advertising_data.get_payload_id()
                )
            )
            logging.getLogger('BlueST').info("Ignoring advertising data.")
            raise e

    @classmethod
    def add_features_to_device(self, device_id, mask_to_features_dict):
        """Add features to a device.

        Register a new device identifier with the corresponding mask-to-features
        dictionary summarizing its available features, or add available features
        to an already registered device, before performing the discovery
        process.

        Otherwise, it is possible to register the feature after discovering a
        device and before connecting to it (see
        :meth:`blue_st_sdk.device.Device.add_external_features()`).

        Args:
            device_id (int): Device identifier.
            mask_to_features_dict  (dict): Mask-to-features dictionary to be added
            to the features decoder dictionary referenced by the device
            identifier. The feature masks of the dictionary must have only one
            bit set to "1".

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidFeatureBitMaskException`
            is raised when a feature is in a non-power-of-two position.
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
            is raised if this method is not run as root.
        """

        # Example:
        # # Adding a 'MyFeature' feature to a Nucleo device and mapping it to a
        # # custom '0x10000000-0001-11e1-ac36-0002a5d5c51b' characteristic.
        # mask_to_features_dict  = {}
        # mask_to_features_dict[0x10000000] = my_feature.MyFeature
        # try:
        #     Manager.add_features_to_device(0x80, mask_to_features_dict)
        # except Exception as e:
        #     logging.getLogger('BlueST').info(e)

        try:
            # Creating Bluetooth Manager.
            manager = Manager.instance()

            # Synchronous discovery of Bluetooth devices.
            manager.discover(False)

            if device_id in self._features_decoder_dict:
                features_decoder = self._features_decoder_dict.get(device_id)
            else:
                features_decoder = {}
                self._features_decoder_dict[device_id] = features_decoder

            features_decoder_to_check = mask_to_features_dict.copy()

            mask = 1
            for i in range(0, 32):
                feature_class = features_decoder_to_check.get(mask)
                if feature_class:
                    features_decoder[mask] = feature_class
                    features_decoder_to_check.pop(mask)
                mask = mask << 1

            if bool(features_decoder_to_check):
                raise BlueSTInvalidFeatureBitMaskException(
                    "Not all keys of the "
                    'mask-to-features dictionary have a single bit set to "1".'
                )
        except BlueSTInvalidOperationException as e:
            raise e

    @classmethod
    def get_device_features(self, device_id):
        """Get a copy of the features map available for the given device
        identifier.
        Used with BlueST protocol v1.

        Args:
            device_id (int): Device identifier.

        Returns:
            dict: A copy of the features map available for the given device
            identifier if found, the base features map otherwise.
        """
        if device_id in self._features_decoder_dict:
            return self._features_decoder_dict[device_id].copy()
        return FeatureCharacteristic.BASE_MASK_TO_FEATURE_DICT.copy()

    def add_listener(self, listener):
        """Add a listener.

        Args:
            listener (:class:`blue_st_sdk.manager.ManagerListener`): Listener to
            be added.
        """
        if listener:
            with lock(self):
                if not listener in self._listeners:
                    self._listeners.append(listener)

    def remove_listener(self, listener):
        """Remove a listener.

        Args:
            listener (:class:`blue_st_sdk.manager.ManagerListener`): Listener to
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


# INTERFACES

class ManagerListener(object):
    """Interface used by the :class:`blue_st_sdk.manager.Manager` class to
    notify that a new Device has been discovered or that the scanning has
    started/stopped.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def on_discovery_change(self, manager, enabled):
        """This method is called whenever a discovery process starts or stops.

        Args:
            manager (:class:`blue_st_sdk.manager.Manager`): Manager instance
            that starts/stops the process.
            enabled (bool): True if a new discovery starts, False otherwise.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError(
            'You must implement "on_discovery_change()" '
            'to use the "ManagerListener" class.'
        )

    @abstractmethod
    def on_device_discovered(self, manager, device, error_message=False):
        """This method is called whenever a device is discovered.

        Args:
            manager (:class:`blue_st_sdk.manager.Manager`): Manager instance
            that discovers the device.
            device (:class:`blue_st_sdk.device.Device`): New device discovered.
            error_message (str): Error message in case the advertisement data
            is not valid.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError(
            'You must implement "on_device_discovered()" '
            'to use the "ManagerListener" class.'
        )

    @abstractmethod
    def on_advertising_data_updated(self, manager, device, advertising_data):
        """This method is called whenever an advertising data has updated.

        Args:
            manager (:class:`blue_st_sdk.manager.Manager`): Manager instance
            that discovers the device.
            device (:class:`blue_st_sdk.device.Device`): Device whose advertising data
            has updated.
            advertising_data (:class:`blue_st_sdk.advertising_data.blue_st_advertising_data.BlueSTAdvertisingData`):
            BlueST advertising data object.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError(
            'You must implement "on_advertising_data_updated()" '
            'to use the "ManagerListener" class.'
        )

    @abstractmethod
    def on_advertising_data_unchanged(self, manager, device, advertising_data):
        """This method is called whenever an advertising data has been received
        but has not changed.

        Args:
            manager (:class:`blue_st_sdk.manager.Manager`): Manager instance
            that discovers the device.
            device (:class:`blue_st_sdk.device.Device`): Device whose advertising data
            has not changed.
            advertising_data (:class:`blue_st_sdk.advertising_data.blue_st_advertising_data.BlueSTAdvertisingData`):
            BlueST advertising data object.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError(
            'You must implement "on_advertising_data_unchanged()" '
            'to use the "ManagerListener" class.'
        )
