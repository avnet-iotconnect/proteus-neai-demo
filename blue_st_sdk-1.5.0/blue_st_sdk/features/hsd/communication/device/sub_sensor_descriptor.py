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

from pykson import JsonObject
from pykson import IntegerField
from pykson import FloatField
from pykson import StringField
from pykson import ObjectField
from pykson import ListField

from blue_st_sdk.features.hsd.communication.device.sensor_type import SensorType


# CLASSES

class SamplesPerTimestamp(JsonObject):
    """Samples per timestamp."""

    _min = IntegerField(serialized_name = "min")
    _max = IntegerField(serialized_name = "max")
    data_type = StringField(serialized_name = "dataType")


class SubSensorDescriptor(JsonObject):
    """Sub Sensor Descriptor."""

    identifier = IntegerField(serialized_name = "id")
    sensor_type = ObjectField(SensorType, serialized_name = "sensorType")
    dimensions = IntegerField(serialized_name = "dimensions")
    dimensions_label = ListField(str, serialized_name = "dimensionsLabel")
    unit = StringField(serialized_name = "unit")
    data_type = StringField(serialized_name = "dataType")
    fs = FloatField(serialized_name = "FS")
    odr = FloatField(serialized_name = "ODR")
    samplesPerTs = ObjectField(SamplesPerTimestamp,serialized_name = "samplesPerTs")

    has_integer_value = True if data_type == "int" else False
    has_float_value = True if data_type == "float" else False
    has_text_value = True if data_type == "string" else False
    has_numeric_value = has_float_value or has_integer_value
