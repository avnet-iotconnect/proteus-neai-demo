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


"""blue_st_advertising_data

The blue_st_advertising_data module keeps the information contained within the
advertising data coming from Bluetooth devices implementing the Blue ST protocol.
"""


# IMPORT

from enum import Enum
from blue_st_sdk.advertising_data.ble_advertising_data import BLEAdvertisingData


# CLASSES

class BlueSTProtocol(Enum):
    """BlueST protocol versions."""

    BLUEST_v1_PROTOCOL = 0x01
    """BlueST protocol version v1."""

    BLUEST_v2_PROTOCOL = 0x02
    """BlueST protocol version v2."""

    BLUEST_vLE_PROTOCOL = 0x03
    """BlueST protocol version LE (Low Energy)."""


class BlueSTAdvertisingData(BLEAdvertisingData):
    """Advertising data sent by a device that follows the BlueST protocol."""

    def __init__(
        self,
        name,
        tx_power,
        mac_address,
        device_type,
        device_id,
        firmware_id,
        payload_id,
        protocol_version,
        feature_mask,
        option_bytes,
        sleeping
    ):
        """Constructor.

        Args:
            name (str): The device name.
            tx_power (int): The device transmission power.
            mac_address (str): The device MAC address.
            device_type (:class:`blue_st_sdk.device.DeviceType`): The type of the
            device.
            device_id (int): The device identifier.
            firmware_id (int): The firmware identifier BlueST protocol v2 only.
            protocol_version (int): The device protocol version.
            feature_mask (int): The bitmask that keeps track of the available
            features BlueST protocol v1 only.
            option_bytes (tuple): The tuple of bytes that represent further
            custom information BlueST protocol v2 only.
            sleeping (bool): The device sleeping status.
            payload_id (int): The payload identifier BlueST protocol vLE only.
        """
        # Device name.
        self._name = name

        # Device transmission power.
        self._tx_power = tx_power

        # Device MAC address.
        self._mac_address = mac_address

        # Device type.
        self._device_type = device_type

        # Device identifier.
        self._device_id = device_id

        # Firmware identifier
        # BlueST protocol v2 only.
        self._firmware_id = firmware_id

        # Payload identifier
        # BlueST protocol vLE only.
        self._payload_id = payload_id

        # Device protocol version.
        self._protocol_version = protocol_version

        # Bitmask that keeps track of the available features
        # BlueST protocol v1 only.
        self._feature_mask = feature_mask

        # Further information bytes
        # BlueST protocol v2 only.
        self._option_bytes = option_bytes

        # Sleeping status.
        self._sleeping = sleeping

    def __str__(self):
        """Return a string that describes the advertising data.

        Returns:
            str: A string that describes the advertising data.
        """
        if self._protocol_version == BlueSTProtocol.BLUEST_v1_PROTOCOL.value:
            return "[ Name: {} | MAC address: {} | BlueST protocol: {} | IDs: {} | Feature mask: {} ]".format(
                self._name,
                self._mac_address,
                self._protocol_version,
                hex(self._device_id),
                hex(self._feature_mask)
            )
        elif self._protocol_version == BlueSTProtocol.BLUEST_v2_PROTOCOL.value:
            return "[ Name: {} | MAC address: {} | BlueST protocol: {} | IDs: {} | Option bytes: {} ]".format(
                self._name,
                self._mac_address,
                self._protocol_version,
                (hex(self._device_id),
                hex(self._firmware_id)),
                self._option_bytes
            )
        elif self._protocol_version == BlueSTProtocol.BLUEST_vLE_PROTOCOL.value:
            return "[ Name: {} | MAC address: {} | BlueST protocol: {} | IDs: {} | Payload: {} | Decoded as: {} ]".format(
                self._name,
                self._mac_address,
                self._protocol_version,
                (hex(self._device_id),
                hex(self._firmware_id),
                hex(self._payload_id)),
                self._option_bytes,
                blue_st_sdk.manager.Manager.decode_bluest_le(self)
            )

    def get_name(self):
        """Get the device name.

        Returns:
            str: The device name.
        """
        return self._name

    def get_tx_power(self):
        """Get the device transmission power.

        Returns:
            int: The device transmission power.
        """
        return self._tx_power

    def get_mac_address(self):
        """Get the device MAC address.

        Returns:
            str: The device MAC address.
        """
        return self._mac_address

    def get_device_type(self):
        """Get the device's type.

        Returns:
            The device's type.
        """
        return self._device_type

    def get_device_id(self):
        """Get the device identifier.

        Returns:
            int: The device identifier.
        """
        return self._device_id

    def get_firmware_id(self):
        """Get the firmware identifier
        BlueST protocol v2 only.

        Returns:
            int: The firmware identifier.
        """
        return self._firmware_id

    def get_payload_id(self):
        """Get the payload identifier
        BlueST protocol vLE only.

        Returns:
            int: The payload identifier.
        """
        return self._payload_id

    def get_protocol_version(self):
        """Get the device protocol version.

        Returns:
            int: The device protocol version.
        """
        return self._protocol_version

    def get_feature_mask(self):
        """Get the bitmask that keeps track of the available features
        BlueST protocol v1 only.

        Returns:
            The bitmask that keeps track of the available features.
        """
        return self._feature_mask

    def get_option_bytes(self):
        """Get the list of bytes that represent further custom information
        BlueST protocol v2 only.

        Returns:
            The list of bytes that represent further custom information.
        """
        return self._option_bytes

    def is_sleeping(self):
        """Check whether the device is sleeping.

        Returns:
            True if the device is sleeping, False otherwise.
        """
        return self._sleeping
