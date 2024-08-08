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

from blue_st_sdk.feature import Feature
from blue_st_sdk.feature import Sample
from blue_st_sdk.feature import ExtractedData
from blue_st_sdk.features.field import Field
from blue_st_sdk.features.field import FieldType
from blue_st_sdk.utils.python_utils import lock
from blue_st_sdk.utils.number_conversion import NumberConversion
from blue_st_sdk.utils.blue_st_exceptions import BlueSTInvalidDataException


# CLASSES

class FeatureSTREDL(Feature):
    """The feature handles the data coming from a Machine Learning Core sensor.

    Data is eight bytes long plus one byte of status.
    """

    FEATURE_NAME = "STREDL"
    FEATURE_UNIT = None
    FEATURE_DATA_NAME = "Register_"
    FEATURE_DATA_MAX = 0
    FEATURE_DATA_MIN = 255
    DATA_LENGTH_BYTES = 8
    FEATURE_FIELDS = []
    for i in range(0, DATA_LENGTH_BYTES):
        FEATURE_FIELDS.append(Field(
            FEATURE_DATA_NAME + str(i + 1),
            FEATURE_UNIT,
            FieldType.UInt8,
            FEATURE_DATA_MAX,
            FEATURE_DATA_MIN))

    def __init__(self, device):
        """Constructor.

        Args:
            device (:class:`blue_st_sdk.device.Device`): Device that will send data to
                this feature.
        """
        super(FeatureSTREDL, self).__init__(
            self.FEATURE_NAME,
            device,
            self.FEATURE_FIELDS)

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
        if len(data) - offset < self.DATA_LENGTH_BYTES:
            raise BlueSTInvalidDataException(
                'There are no %d bytes available to read.' \
                % (self.DATA_LENGTH_BYTES))
        sample_data = []
        for i in range(0, self.DATA_LENGTH_BYTES):
            sample_data.append(NumberConversion.byte_to_uint8(data, offset + i))
        sample = Sample(
            sample_data,
            self.get_fields_description(),
            timestamp)
        return ExtractedData(sample, self.DATA_LENGTH_BYTES)

    @classmethod
    def get_register_status(self, sample):
        """Get the register status from a sample.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data.

        Returns:
            list: The register status from a valid sample (list of Integer),
            None otherwise.
        """
        if sample:
            if sample._data:
                output = []
                for i in range(0, self.DATA_LENGTH_BYTES):
                    output.append(sample._data[i])
                return output
        return None

    @classmethod
    def get_register_status_at_index(self, sample, index):
        """Get the register status from a sample at a given index.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data.
            index (int): The index of the register status.

        Returns:
            int: The register status from a valid sample at a given index, <nan>
            otherwise.
        """
        if sample:
            if sample._data:
                return sample._data[index]
        return float('nan')

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

        if len(sample._data) == self.DATA_LENGTH_BYTES:
            return str(self.get_register_status(sample))
        return None
