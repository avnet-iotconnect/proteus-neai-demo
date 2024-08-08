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


"""blue_st_advertising_data_parser

The blue_st_advertising_data_parser module contains tools to parse the
advertising data coming from Bluetooth devices implementing the Blue ST protocol.
"""


# IMPORT

import binascii
import logging
import textwrap

import blue_st_sdk.device
from blue_st_sdk.advertising_data.blue_st_advertising_data import BlueSTProtocol
from blue_st_sdk.advertising_data.blue_st_advertising_data import BlueSTAdvertisingData
from blue_st_sdk.advertising_data.ble_advertising_data_parser import BLEAdvertisingDataParser
from blue_st_sdk.utils.blue_st_exceptions import BlueSTInvalidAdvertisingDataException


# CLASSES

class BlueSTAdvertisingDataParser(BLEAdvertisingDataParser):
    """Advertising data sent by a device that follows the BlueST protocol."""

    # Note: the Bluepy library hides the field-type.
    # Note: Lenghts of "7" and "13" are kept for backward compatibility with the
    #       "old" BlueST protocol version "0x01", which does not have two bytes
    #       for the manufacturer specific identifier (e.g.: "0x0030" for
    #       STMicroelectronics).
    ADVERTISING_DATA_BLUEST_v1_MANUFACTURER_LENGTH_1_bytes = 0x07
    """Length of the advertising data manufacturer in BlueST protocol v1 without
    MAC address."""

    ADVERTISING_DATA_BLUEST_v1_MANUFACTURER_LENGTH_2_bytes = 0x0D
    """Length of the advertising data manufacturer in BlueST protocol v1 with
    MAC address."""

    ADVERTISING_DATA_BLUEST_v2_MANUFACTURER_LENGTH_1_bytes = 0x09
    """Length of the advertising data manufacturer in BlueST protocol v2 without
    MAC address."""

    ADVERTISING_DATA_BLUEST_v2_MANUFACTURER_LENGTH_2_bytes = 0x0F
    """Length of the advertising data manufacturer in BlueST protocol v2 with
    MAC address."""

    ADVERTISING_DATA_BLUEST_vLE_MANUFACTURER_LENGTH_1_bytes = 0x08
    """Minimum length of the advertising data manufacturer in BlueST protocol vLE."""

    ADVERTISING_DATA_BLUEST_vLE_MANUFACTURER_LENGTH_2_bytes = 0x1E
    """Maximum length of the advertising data manufacturer in BlueST protocol vLE."""

    ADVERTISING_DATA_BLUEST_v1_FEATURE_MASK_bytes = 4
    """Lenght of the feature mask in BlueST protocol v1."""

    PROTOCOL_VERSION_SUPPORTED_MIN = 0x01
    """Minimum version of the BlueST protocol supported."""

    PROTOCOL_VERSION_SUPPORTED_MAX = 0x03
    """Maximum version of the BlueST protocol supported."""

    STM_MANUFACTURER_ID_LOW_BYTE = 0x30
    """Low byte of STMicroelectronics manufacturer identifier."""

    STM_MANUFACTURER_ID_HIGH_BYTE = 0x00
    """High byte of STMicroelectronics manufacturer identifier."""

    STM_MANUFACTURER_OFFSET_bytes = 4
    """STMicroelectronics manufacturer offset."""

    _NO_NAME = "NO_NAME"
    """Default name of a device with no name specified within the advertising
    data."""

    _COMPLETE_LOCAL_NAME = 0x09
    """Code identifier for the complete local name."""

    _TX_POWER = 0x0A
    """Code identifier for the transmission power."""

    _MANUFACTURER_SPECIFIC_DATA = 0xFF
    """Code identifier that a proprietary manufacturer advertisement data will follow."""
    """
    Examples:
    09 FF 30 00 02 09 04 00 00 00 fccd1283b72a
    09 FF 01 06 04 ff 15 7f c0a3bbaf5c5c
    """

    @classmethod
    def parse(self, ble_advertising_data):
        """Parse the BLE advertising data.

        Args:
            ble_advertising_data (list): BLE advertising data,
            as scanned by the bluepy library.
            Is a list of tuples (adtype, description, value) containing the AD type code,
            human-readable description and value for all available advertising data items.

        Returns:
            :class:`blue_st_sdk.advertising_data.ble_advertising_data.BLEAdvertisingData`:
            The advertising data information sent by the device.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidAdvertisingDataException`
            is raised if the advertising data is not well formed.
        """
        # Getting data fields out of the received advertising data.
        try:
            name = self._NO_NAME
            tx_power = -1
            manufacturer_specific_data = None
            manufacturer_offset = 0
            mac_address_in_advertising_data = None
            mac_address_in_advertising_data_flag = False
            device_id = -1
            firmware_id = -1
            payload_id = -1
            option_bytes = []
            device_type = blue_st_sdk.device.DeviceType.GENERIC
            protocol_version = -1
            feature_mask = -1
            sleeping = False

            #logging.getLogger('BlueST').info('New device:')
            for adtype, description, value in ble_advertising_data:
                #logging.getLogger('BlueST').info('\tBLE frame:\n\t\tadtype: {}\n\t\tdescription: {}\n\t\tvalue: {}'.format(
                #    hex(adtype), description, value))
                if adtype == self._COMPLETE_LOCAL_NAME:
                    name = value
                elif adtype == self._TX_POWER:
                    tx_power = value
                elif adtype == self._MANUFACTURER_SPECIFIC_DATA:
                    manufacturer_specific_data = value

            # Checking the presence of the manufacturer specific data.
            if manufacturer_specific_data is None:
                raise BlueSTInvalidAdvertisingDataException(
                    'BlueST protocol error: missing manufacturer specific data.'
                )

            # Getting the length of the manufacturer specific data.
            # Adding 1 byte of the field-type, which is hidden by the Bluepy library.
            # Python 2.7
            # manufacturer_specific_data_length = len(manufacturer_specific_data.decode('hex')) + 1
            # Python 3.5
            manufacturer_specific_data_length = \
                len(binascii.unhexlify(manufacturer_specific_data.encode("utf-8"))) + 1

            # Checking the length of the manufacturer specific data
            # and the manufacturer identifier.
            if not (
                manufacturer_specific_data_length == self.ADVERTISING_DATA_BLUEST_v1_MANUFACTURER_LENGTH_1_bytes or \
                manufacturer_specific_data_length == self.ADVERTISING_DATA_BLUEST_v1_MANUFACTURER_LENGTH_2_bytes or \
                manufacturer_specific_data_length == self.ADVERTISING_DATA_BLUEST_v2_MANUFACTURER_LENGTH_1_bytes or \
                manufacturer_specific_data_length == self.ADVERTISING_DATA_BLUEST_v2_MANUFACTURER_LENGTH_2_bytes or \
                (
                    manufacturer_specific_data_length >= self.ADVERTISING_DATA_BLUEST_vLE_MANUFACTURER_LENGTH_1_bytes and \
                    manufacturer_specific_data_length <= self.ADVERTISING_DATA_BLUEST_vLE_MANUFACTURER_LENGTH_2_bytes
                )
            ):
                raise BlueSTInvalidAdvertisingDataException(
                    'BlueST protocol error: advertising data packet length "{}" not allowed.'.format(
                        str(manufacturer_specific_data_length)
                    )
                )

            # This might be a BlueST protocol advertising data packet.
            # Let's check the next bytes.

            # From v2 onwards, the manufacturer identifier follows, while
            # v1 does't have it and the protocol version follows instead.
            header_byte0 = int(manufacturer_specific_data[0:2], 16)
            header_byte1 = int(manufacturer_specific_data[2:4], 16)
            if header_byte0 == BlueSTProtocol.BLUEST_v1_PROTOCOL.value:
                # It might be a device with BlueST protocol version v1.
                pass
            elif (
                header_byte0 == self.STM_MANUFACTURER_ID_LOW_BYTE and \
                header_byte1 == self.STM_MANUFACTURER_ID_HIGH_BYTE
            ):
                # It might be a device with BlueST protocol version v2 onwards.
                pass
            else:
                raise BlueSTInvalidAdvertisingDataException(
                    'BlueST protocol error: manufacturer identifier "{}" not recognized.'.format(
                        str(manufacturer_specific_data[2:4]) + str(manufacturer_specific_data[0:2])
                    )
                )

            # This is a BlueST protocol advertising data packet.

            # Setting manufacturer offset.
            if (
                manufacturer_specific_data_length == self.ADVERTISING_DATA_BLUEST_v2_MANUFACTURER_LENGTH_1_bytes or \
                manufacturer_specific_data_length == self.ADVERTISING_DATA_BLUEST_v2_MANUFACTURER_LENGTH_2_bytes or \
                (
                    manufacturer_specific_data_length >= self.ADVERTISING_DATA_BLUEST_vLE_MANUFACTURER_LENGTH_1_bytes and \
                    manufacturer_specific_data_length <= self.ADVERTISING_DATA_BLUEST_vLE_MANUFACTURER_LENGTH_2_bytes
                )
            ):
                manufacturer_offset = self.STM_MANUFACTURER_OFFSET_bytes

            # Setting MAC address flag.
            if (
                manufacturer_specific_data_length == self.ADVERTISING_DATA_BLUEST_v1_MANUFACTURER_LENGTH_2_bytes or \
                manufacturer_specific_data_length == self.ADVERTISING_DATA_BLUEST_v2_MANUFACTURER_LENGTH_2_bytes
            ):
                mac_address_in_advertising_data_flag = True

            # Getting BlueST protocol version.
            protocol_version = int(manufacturer_specific_data[manufacturer_offset : manufacturer_offset + 2], 16)
            if (
                protocol_version < self.PROTOCOL_VERSION_SUPPORTED_MIN or \
                protocol_version > self.PROTOCOL_VERSION_SUPPORTED_MAX
            ):
                raise BlueSTInvalidAdvertisingDataException(
                    'BlueST protocol error: version "{}" not supported; it has to be in [{}..{}].'.format(
                        str(protocol_version),
                        str(self.PROTOCOL_VERSION_SUPPORTED_MIN),
                        str(self.PROTOCOL_VERSION_SUPPORTED_MAX)
                    )
                )

            # Getting other information from the manufacturer specific data
            # based on the BlueST protocol version.
            device_id = int(manufacturer_specific_data[manufacturer_offset + 2 : manufacturer_offset + 4], 16)
            # device_id = device_id & 0xFF \
            #    if device_id & 0x80 == 0x80 else device_id & 0x1F
            device_type = self._get_device_type(device_id)
            sleeping = self._get_device_sleeping_status(int(manufacturer_specific_data[manufacturer_offset + 2 : manufacturer_offset + 4], 16))
            if protocol_version == BlueSTProtocol.BLUEST_v1_PROTOCOL.value:
                feature_mask = int(manufacturer_specific_data[manufacturer_offset + 4 : manufacturer_offset + 4 + 2 * self.ADVERTISING_DATA_BLUEST_v1_FEATURE_MASK_bytes], 16)
            elif protocol_version == BlueSTProtocol.BLUEST_v2_PROTOCOL.value:
                firmware_id = int(manufacturer_specific_data[8:10], 16)
                option_bytes.append(int(manufacturer_specific_data[10:12], 16))
                option_bytes.append(int(manufacturer_specific_data[12:14], 16))
                option_bytes.append(int(manufacturer_specific_data[14:16], 16))
            elif protocol_version == BlueSTProtocol.BLUEST_vLE_PROTOCOL.value:
                firmware_id = int(manufacturer_specific_data[8:10], 16)
                payload_id = int(manufacturer_specific_data[10:12], 16)
                for byte in textwrap.wrap(manufacturer_specific_data[12:], 2):
                    option_bytes.append(int(byte, 16))
            # Get the MAC address in case it is transmitted in the advertising data,
            # but don't use it for the moment.
            if mac_address_in_advertising_data_flag:
                mac_address_in_advertising_data = manufacturer_specific_data[manufacturer_offset + 12 : manufacturer_offset + 24]

            # Returning a BlueST advertising data object.
            return BlueSTAdvertisingData(
                name,
                tx_power,
                mac_address_in_advertising_data,
                device_type,
                device_id,
                firmware_id,
                payload_id,
                protocol_version,
                feature_mask,
                tuple(option_bytes),
                sleeping
            )

        except TypeError as e:
            return None

    @classmethod
    def _get_device_type(self, device_id):
        """Get the device's type.

        Args:
            device_id (int): Device identifier.

        Returns:
            :class:`blue_st_sdk.device.DeviceType`: The device's type.
        """
        device_id = int(device_id & 0xFF)
        if (
            (device_id >= 0x10 and device_id <= 0x7E) or \
            (device_id == 0x7F) or \
            (device_id >= 0x81 and device_id <= 0x8A) or \
            (device_id >= 0x8B and device_id <= 0x8F) or \
            (device_id >= 0x90 and device_id <= 0xFF)
        ):
            return blue_st_sdk.device.DeviceType.GENERIC
        return blue_st_sdk.device.DeviceType(device_id)

    @classmethod
    def _get_device_sleeping_status(self, device_type):
        """Parse the device type field to check whether the device is sleeping.

        Args:
            device_type (int): Device type.

        Returns:
            True if the device is sleeping, False otherwise.
        """
        return (device_type & 0x80) != 0x80 and ((device_type & 0x40) == 0x40)
