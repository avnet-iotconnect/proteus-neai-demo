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


# IMPORT

import struct

from blue_st_sdk.feature import Feature
from blue_st_sdk.feature import Sample
from blue_st_sdk.feature import ExtractedData
from blue_st_sdk.features.field import Field
from blue_st_sdk.features.field import FieldType
from blue_st_sdk.features.hsd.communication.device.device_parser import DeviceParser
from blue_st_sdk.features.hsd.communication.device.sensor_status import SensorStatusWithId
from blue_st_sdk.utils.stl_to_transport_protocol import STL2TransportProtocol
from blue_st_sdk.utils.blue_st_exceptions import BlueSTInvalidOperationException
from blue_st_sdk.utils.blue_st_exceptions import BlueSTInvalidDataException


# CLASSES

class FeatureHSDatalogConfig(Feature):
    """The feature handles the configuration of an High Speed Datalog device."""

    FEATURE_NAME = "HS Datalog Config (TBC)"
    FEATURE_UNIT = None
    FEATURE_DATA_NAME = "HSDatalogConfig"
    FEATURE_DATA_MAX = +128
    FEATURE_DATA_MIN = -127
    FEATURE_FIELDS = Field(
        FEATURE_DATA_NAME,
        FEATURE_UNIT,
        FieldType.ByteArray,
        FEATURE_DATA_MAX,
        FEATURE_DATA_MIN)
    DATA_LENGTH_BYTES = -1
    SCALE_FACTOR = -1

    #LATEST_FW_VERSION = "1.2.0"
    #LATEST_FW_NAME = "FP-SNS-DATALOG1"
    #LATEST_FW_URL = "https://www.st.com/en/embedded-software/fp-sns-datalog1.html"

    def __init__(self, device):
        """Constructor.

        Args:
            device (:class:`blue_st_sdk.device.Device`): Device that will send data to
                this feature.
        """
        super(FeatureHSDatalogConfig, self).__init__(
            self.FEATURE_NAME,
            device,
            [self.FEATURE_FIELDS])

        # Transport decoder.
        self._transport_decoder = STL2TransportProtocol(device.get_mtu_bytes())

    def _extract_data(self, timestamp, data, offset):
        """Extract the data from the feature's raw data.

        Args:
            timestamp (int): Data's timestamp.
            data (str): The data read from the feature.
            offset (int): Offset where to start reading data.
        
        Returns:
            :class:`blue_st_sdk.feature.ExtractedData`: Container of the number
            of bytes read and the extracted data.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidDataException`
                if the data array has not enough data to read.
        """
        # if len(data) - offset < self.DATA_LENGTH_BYTES:
        #     raise BlueSTInvalidDataException(
        #         'There are no %d bytes available to read.' \
        #         % (self.DATA_LENGTH_BYTES))
        command_json_str = self._transport_decoder.decapsulate(data)
        if command_json_str:
            command_json_object = DeviceParser.to_json_object(command_json_str)
            command_data = ConfigurationSample()
                #DeviceParser.extract_device(command_json_object),
                #DeviceParser.extract_device_status(command_json_object))
            return ExtractedData(command_data, len(data))
        return ExtractedData(None, len(data))

    def _get_device_model(self, sample):
        """Get the device model that the configuration sample refers to.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): A configuration sample.

        Returs:
            :class:`blue_st_sdk.features.high_speed_datalog.communication.device.device_model.DeviceModel`:
            The device model that the configuration sample refers to.
        """
        if not sample:
            return None
        if isinstance(sample, self.ConfigurationSample):
            return sample.get_device_model()

    def _get_device_status(self, sample):
        """Get the device status that the configuration sample refers to.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): A configuration sample.

        Returs:
            :class:`blue_st_sdk.features.high_speed_datalog.communication.device_status.DeviceStatus`:
            The device status that the configuration sample refers to.
        """
        if not sample:
            return None
        if isinstance(sample, self.ConfigurationSample):
            return sample.get_device_status()

    def _send_data(self, data):
        """Synchronous request to write data to the feature.

        Args:
            data (str): Raw data to write.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
            is raised if the feature is not enabled or the operation
            required is not supported.
        """
        try:
            bytes_sent = 0
            while bytes_sent < len(data):
                bytes_to_send = min(
                    STL2TransportProtocol._MTU_bytes,
                    len(data) - bytes_sent
                )
                data_to_send = data[bytes_sent:bytes_sent + bytes_to_send]
                self._write_data(data_to_send)
                bytes_sent += bytes_to_send
        except BlueSTInvalidOperationException as e:
            raise e

    def send_command(self, command_json_object=None):
        """Synchronous request to write a command to the feature.

        Args:
            command_json_object (:class:`blue_st_sdk.features.high_speed_datalog.commmunication.hsd_command.HSDCommand`):
                Command to write.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
            is raised if the feature is not enabled or the operation
            required is not supported.
        """
        try:
            command_json_str = DeviceParser.to_json_str(command_json_object)
            command_json_bytes = self._transport_decoder.encapsulate(command_json_str)
            self._send_data(command_json_bytes)
        except BlueSTInvalidOperationException as e:
            raise e

    def get_device_information(self, sample):
        """Get information from the device model that the configuration sample
        refers to.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): A configuration sample.

        Returs:
            :class:`blue_st_sdk.features.high_speed_datalog.communication.device.device_information.DeviceInformation`:
            The device information that the configuration sample refers to.
        """
        return self._get_device_model(sample).device_information

    def get_device_tag_configuration(self, sample):
        """Get tag configuration from the device model that the configuration
        sample refers to.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): A configuration sample.

        Returs:
            :class:`blue_st_sdk.features.high_speed_datalog.communication.device.tag.TagConfiguration`:
            The tag configuration that the configuration sample refers to.
        """
        return self._get_device_model(sample).tag_configuration

    def is_logging(self, sample):
        """Check whether the device is logging from the device status that the
        configuration sample refers to.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): A configuration sample.

        Returs:
            boolean: True if the device is logging, False otherwise.
        """
        return self._get_device_status(sample).is_sd_logging

    def is_sd_card_inserted(self, sample):
        """Check whether the SD card is inserted into the device from the device
        status that the configuration sample refers to.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): A configuration sample.

        Returs:
            boolean: True if the SD card is inserted into the device, False
            otherwise.
        """
        return self._get_device_status(sample).is_sd_card_inserted

    def get_sensor_status_with_id(self, sample):
        """Get the status of the sensor build from the device status that the
        configuration sample refers to.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): A configuration sample.

        Returs:
            :class:`blue_st_sdk.features.high_speed_datalog.communication.device.sensor_status.SensorStatusWithId`:
            The status of the sensor that the configuration sample refers to.
        """
        sensor_id = self._get_device_status(sample).sensor_id
        sensor_status = self._get_device_status(sample).sensor_status
        if sensor_id == None or sensor_status == None:
            return None
        return SensorStatusWithId(sensor_id, sensor_status)


class ConfigurationSample(Sample):
    """Configuration Sample from a device."""
    
    def __init__(self, device_model=None, device_status=None):
        """Constructor.

        Args:
            device_model (:class:`blue_st_sdk.features.high_speed_datalog.communication.device.device_model.DeviceModel`):
                Device model that the configuration sample refers to.
            device_status (:class:`blue_st_sdk.features.high_speed_datalog.communication.device_status.DeviceStatus`):
                Status of the configuration of the device.
        """
        super(Sample, self).__init__(None, FeatureHSDatalogConfig.FEATURE_FIELDS)
        self._device_model = device_model
        self._device_status = device_status

    def get_device_model(self):
        """Get the device model that the configuration sample refers to.

        Returs:
            :class:`blue_st_sdk.features.high_speed_datalog.communication.device.device_model.DeviceModel`:
            The device model that the configuration sample refers to.
        """
        return self._device_model

    def get_device_status(self):
        """Get the device status that the configuration sample refers to.

        Returs:
            :class:`blue_st_sdk.features.high_speed_datalog.communication.device_status.DeviceStatus`:
            The device status that the configuration sample refers to.
        """
        return self._device_status
