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

import json
import logging

from blue_st_sdk.feature import Feature
from blue_st_sdk.feature import Sample
from blue_st_sdk.feature import ExtractedData
from blue_st_sdk.features.field import Field
from blue_st_sdk.features.field import FieldType
from blue_st_sdk.utils.python_utils import lock
from blue_st_sdk.utils.json_utils import *
from blue_st_sdk.utils.stl_to_transport_protocol import STL2TransportProtocol
from blue_st_sdk.utils.blue_st_exceptions import BlueSTInvalidOperationException
from blue_st_sdk.utils.payload_parser import PayloadParser


# CLASSES

class FeaturePnPLike(Feature):
    """The feature handles the PnPLike protocol."""

    FEATURE_NAME = "PnPLike"
    FEATURE_DEVICES_JSON_KEY = "devices"
    FEATURE_UNIT = ""
    FEATURE_DATA_NAME = "PnPLike"
    FEATURE_DATA_MAX = 0
    FEATURE_DATA_MIN = 0
    DATA_LENGTH_BYTES = 0
    SCALE_FACTOR = 10.0
    FEATURE_FIELDS = Field(
        FEATURE_DATA_NAME,
        FEATURE_UNIT,
        FieldType.PnPLDevice,
        FEATURE_DATA_MAX,
        FEATURE_DATA_MIN)

    def __init__(self, device):
        """Constructor.

        Args:
            device (:class:`blue_st_sdk.device.Device`): Device that will send data to
                this feature.
        """
        super(FeaturePnPLike, self).__init__(
            self.FEATURE_NAME,
            device,
            [self.FEATURE_FIELDS])

        # Transport decoder.
        self._transport_decoder = STL2TransportProtocol(device.get_mtu_bytes())

        """
        private val json = Json {
            ignoreUnknownKeys = true
            explicitNulls = false
        }
        """

    def __str__(self):
        """Get a string representing the last sample.

        Return:
            str: A string representing the last sample.
        """
        with lock(self):
            sample = self._last_sample

        if sample:
            return sample
        return None

    def _extract_data(self, timestamp, data, offset):
        """Extract the data from the feature's raw data.

        Args:
            timestamp (int): Data's timestamp.
            data (bytearray): The data read from the feature.
            offset (int): Offset where to start reading data.
        
        Returns:
            :class:`blue_st_sdk.feature.ExtractedData`: Container of the number
            of bytes read and the extracted data.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidDataException`
                if the data array has not enough data to read.
        """
        decapsulated_data = self._transport_decoder.decapsulate(data)
        if decapsulated_data:
            if is_json_str(decapsulated_data):
                #data_json_object = json.loads(decapsulated_data)
                #logging.getLogger('BlueST').info("Received PnPL reponse:\n{}.".format(data_json_object))
                #data_json_object = PayloadParser.to_json_object(decapsulated_data, DeviceStatus)
                #command_data = ConfigurationSample()
                #DeviceParser.extract_device(data_json_object),
                #DevicedParser.extract_device_status(data_json_object))
                return ExtractedData(decapsulated_data, len(decapsulated_data))
        return ExtractedData(None, 0)
        # The following return value can be used instead only for debug purpose,
        # as an alternative to the previous one.
        #return ExtractedData(data[1:].decode('unicode_escape'), len(data) - 1)

    def _send_data(self, data):
        """Synchronous request to write data to the feature.

        Args:
            data (bitearray): Raw data to write.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
            is raised if the feature is not enabled or the operation
            required is not supported.
        """
        try:
            bytes_sent = 0
            while bytes_sent < len(data):
                bytes_to_send = min(
                    self._transport_decoder.get_mtu_bytes(),
                    len(data) - bytes_sent
                )
                data_to_send = data[bytes_sent:bytes_sent + bytes_to_send]
                self._write_data(data_to_send)
                bytes_sent += bytes_to_send
        except BlueSTInvalidOperationException as e:
            raise e

    def send_command(self, command_json_str):
        """Send a command.

        Args:
            command_json_str (str): The JSON command as a string.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
                is raised if the feature is not enabled or the operation
                required is not supported.
        """
        try:
            #command_json_str = DeviceParser.to_json_str(command_json_object)
            command_json_bytes = self._transport_decoder.encapsulate(command_json_str)
            self._send_data(command_json_bytes)
        except BlueSTInvalidOperationException as e:
            raise e

"""
    override fun extractData(
        timeStamp: Long,
        data: ByteArray,
        dataOffset: Int
    ): FeatureUpdate<PnPLConfig> {
        var deviceStatus: PnPLDevice? = null

        stl2TransportProtocol.decapsulate(data)
            ?.toString(Charsets.UTF_8)
            ?.dropLast(1)
            ?.let { jsonString ->
                jsonString.logJson(tag = TAG)

                deviceStatus = extractDeviceStatus(jsonString)
            }

        return FeatureUpdate(
            readByte = data.size,
            timeStamp = timeStamp,
            rawData = data,
            data = PnPLConfig(
                deviceStatus = FeatureField(
                    name = "DeviceStatus",
                    value = deviceStatus
                )
            )
        )
    }

    private fun extractDeviceStatus(jsonString: String): PnPLDevice? = try {
        val jsonObject = json.decodeFromString<JsonObject>(jsonString)
        if (jsonObject.containsKey(DEVICES_JSON_KEY)) {
            json.decodeFromJsonElement<PnPLResponse>(jsonObject).devices.firstOrNull()
        } else {
            PnPLDevice(
                boardId = null,
                fwId = null,
                serialNumber = null,
                components = listOf(jsonObject)
            )
        }
    } catch (ex: Exception) {
        Log.w(TAG, ex.message, ex)

        null
    }

    private fun extractComponentStatus(jsonString: String): JsonObject? = try {
        json.decodeFromString<JsonObject>(jsonString)
    } catch (ex: Exception) {
        Log.w(TAG, ex.message, ex)

        null
    }

    override fun packCommandData(featureBit: Int?, command: FeatureCommand): ByteArray? =
        when (command) {
            is PnPLCommand ->
                stl2TransportProtocol.encapsulate(command.cmd.jsonString)
            else -> null
        }

    override fun parseCommandResponse(data: ByteArray): FeatureResponse? = null
}
"""
