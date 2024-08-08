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

from enum import Enum
import logging
import struct
import inspect
from pathlib import Path 
from bluepy.btle import BTLEException
import sys
import json
from blue_st_sdk.feature import Feature
from blue_st_sdk.feature import Sample
from blue_st_sdk.feature import ExtractedData
from blue_st_sdk.features.field import Field
from blue_st_sdk.features.field import FieldType
from blue_st_sdk.utils.python_utils import lock
from blue_st_sdk.utils.number_conversion import NumberConversion
from blue_st_sdk.utils.number_conversion import LittleEndian
from blue_st_sdk.utils.blue_st_exceptions import BlueSTInvalidOperationException
from blue_st_sdk.utils.blue_st_exceptions import BlueSTInvalidDataException
sys.path.append("/home/weston/proteus_stuff/STM32MP157F_Demo")
import plugin_queue

# CLASSES

class Phase(Enum):
    """Phase of the AI engine."""
    IDLE = 0x00
    LEARNING = 0x01
    DETECTION = 0x02
    IDLE_TRAINED = 0x03
    BUSY = 0x04
    NONE = 0xFF

    def __str__(self):
        return self.name


class State(Enum):
    """State of the AI engine."""
    OK = 0x00
    INIT_NOT_CALLED = 0x7B
    BOARD_ERROR = 0x7C
    KNOWLEDGE_ERROR = 0x7D
    NOT_ENOUGH_LEARNING = 0x7E
    MINIMAL_LEARNING_DONE = 0x7F
    UNKNOWN_ERROR = 0x80
    NONE = 0xFF

    def __str__(self):
        return self.name


class Status(Enum):
    """Status of the signal."""
    NORMAL = 0x00
    ANOMALY = 0x01
    NONE = 0xFF

    def __str__(self):
        return self.name


class Command(Enum):
    """Commands to the AI engine."""
    STOP = 0x00
    LEARN = 0x01
    DETECT = 0x02
    RESET = 0xFF

    def __str__(self):
        return self.name


class FeatureNEAIAnomalyDetection(Feature):
    """The feature handles the NanoEdge AI Anomaly Detection capability."""

    FEATURE_NAME = "NEAIAnomalyDetection"
    DATA_LENGTH_BYTES = 5
    TIMESTAMP_DATA_LENGTH_BYTES = 4
    PHASE_INDEX = 0
    STATE_INDEX = 1
    PROGRESS_INDEX = 2
    STATUS_INDEX = 3
    SIMILARITY_INDEX = 4

    def __init__(self, device):
        """Constructor.

        Args:
            device (:class:`blue_st_sdk.device.Device`): Device that will send data to
                this feature.
        """
        super(FeatureNEAIAnomalyDetection, self).__init__(
            self.FEATURE_NAME,
            device,
            [
                Field("Phase", "", FieldType.UInt8, None, None),
                Field("State", "", FieldType.UInt8, None, None),
                Field("Progress", "", FieldType.UInt8, 0, 100),
                Field("Status", "", FieldType.UInt8, None, None),
                Field("Similarity", "", FieldType.UInt8, 0, 100)
            ]
        )

    def __str__(self):
        """Get a string representing the last sample.

        Return:
            str: A string representing the last sample.
        """
        with lock(self):
            sample = self._last_sample

        if not sample:
            return self._name
        if not sample._data:
            return self._name

        result = ''
        if len(sample._data) >= self.DATA_LENGTH_BYTES:
            #result = '{}({}):  [ Phase: {} | State: {} | Progress: {} | Status {} | Similarity: {} ]'.format(
            result = '{}:  [ Phase: {} | State: {} | Progress: {} | Status {} | Similarity: {} ]'.format(
                self._name,
                #sample._timestamp,
                str(self.get_phase(sample)),
                str(self.get_state(sample)),
                str(self.get_progress(sample)),
                str(self.get_status(sample)),                   
                str(self.get_similarity(sample)))
            dict = {}
            dict["phase"] = str(self.get_phase(sample))
            dict["state"] = str(self.get_state(sample))
            dict["progress"] = int(str(self.get_progress(sample)))
            dict["status"] = str(self.get_status(sample))
            dict["similarity"] = int(str(self.get_similarity(sample)))
            with open("/home/weston/proteus_stuff/STM32MP157F_Demo/upstream_data.json","w") as upstream_file:
                json.dump(dict, upstream_file)
        return result

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
        #logging.getLogger('BlueTS').info('Receiving data: {}'.format(data))
        #if len(data) - offset < self.DATA_LENGTH_BYTES:
        if len(data) - self.TIMESTAMP_DATA_LENGTH_BYTES < self.DATA_LENGTH_BYTES:
            raise BlueSTInvalidDataException(
                'There are no %s bytes available to read.' \
                % (self.DATA_LENGTH_BYTES))
        #if len(data) - offset == self.DATA_LENGTH_BYTES:
        if len(data) - self.TIMESTAMP_DATA_LENGTH_BYTES == self.DATA_LENGTH_BYTES:
            # Extract the activity from the feature's raw data.
            sample = Sample(
                [NumberConversion.byte_to_uint8(data, i) for i in range(self.TIMESTAMP_DATA_LENGTH_BYTES, self.TIMESTAMP_DATA_LENGTH_BYTES + self.DATA_LENGTH_BYTES)],
                self.get_fields_description(),
                timestamp)
            return ExtractedData(sample, self.DATA_LENGTH_BYTES)

    def get_phase(self, sample):
        """Getting the phase from a sample.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data.

        Returns:
            :class:`Phase`: The recognized phase if the sample is
            valid, "None" otherwise.
        """
        if sample:
            if sample._data:
                if sample._data[self.PHASE_INDEX] is not None:
                    return Phase(NumberConversion.byte_to_uint8(sample._data, self.PHASE_INDEX))
        return None

    def get_state(self, sample):
        """Getting the state from a sample.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data.

        Returns:
            :class:`State`: The recognized state if the sample is
            valid, "None" otherwise.
        """
        if sample:
            if sample._data:
                if sample._data[self.STATE_INDEX] is not None:
                    return State(NumberConversion.byte_to_uint8(sample._data, self.STATE_INDEX))
        return None

    def get_progress(self, sample):
        """Getting the progress from a sample.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data.

        Returns:
            int: The recognized progress if the sample is
            valid, "None" otherwise.
        """
        if sample:
            if sample._data:
                if sample._data[self.PROGRESS_INDEX] is not None:
                    return int(NumberConversion.byte_to_uint8(sample._data, self.PROGRESS_INDEX))
        return None

    def get_status(self, sample):
        """Getting the status from a sample.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data.

        Returns:
            :class:`Status`: The recognized status if the sample is
            valid, "None" otherwise.
        """
        if sample:
            if sample._data:
                if sample._data[self.STATUS_INDEX] is not None:
                    return Status(NumberConversion.byte_to_uint8(sample._data, self.STATUS_INDEX))
        return None

    def get_similarity(self, sample):
        """Getting the similarity from a sample.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data.

        Returns:
            int: The recognized similarity if the sample is
            valid, "None" otherwise.
        """
        if sample:
            if sample._data:
                if sample._data[self.SIMILARITY_INDEX] is not None:
                    return int(NumberConversion.byte_to_uint8(sample._data, self.SIMILARITY_INDEX))
        return None

    def _send_command(self, command):
        """Send a command.

        Args:
            command (:class:`Command`):
                The command to be sent.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
                is raised if the feature is not enabled or the operation
                required is not supported.
        """
        command_bytes = struct.pack(
            #'=LBL',
            #0,
            '=BL',
            int(command.value),
            0)

        try:
            #logging.getLogger('BlueTS').info('Sending command: {}'.format(command_bytes))
            self._write_data(command_bytes)
        except BlueSTInvalidOperationException as e:
            raise e

    def stop(self):
        """Send stop command.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
                is raised if the feature is not enabled or the operation
                required is not supported.
        """
        self._send_command(Command.STOP)

    def learn(self):
        """Send learn command.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
                is raised if the feature is not enabled or the operation
                required is not supported.
        """
        self._send_command(Command.LEARN)

    def detect(self):
        """Send detect command.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
                is raised if the feature is not enabled or the operation
                required is not supported.
        """
        self._send_command(Command.DETECT)

    def reset(self):
        """Send reset command.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
                is raised if the feature is not enabled or the operation
                required is not supported.
        """
        self._send_command(Command.RESET)
