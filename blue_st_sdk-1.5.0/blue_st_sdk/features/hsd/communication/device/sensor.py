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
from pykson import StringField
from pykson import ObjectField

from blue_st_sdk.features.hsd.communication.device.sensor_status import SensorStatus
from blue_st_sdk.features.hsd.communication.device.sensor_descriptor import SensorDescriptor


# CLASSES

class Sensor(JsonObject):
    """Sensor Information."""

    identifier = IntegerField(serialized_name = "id")
    name = StringField(serialized_name = "name")
    sensor_descriptor = ObjectField(SensorDescriptor, serialized_name = "sensorDescriptor")
    sensor_status = ObjectField(SensorStatus, serialized_name = "sensorStatus")

    def compare_to(self, other):
        return identifier - other.identifier

    def get_sub_sensor_status_with_id(self, identifier):
        for sub_sensor_descriptor in sensor_descriptor.sub_sensor_descriptors:
            if sub_sensor_descriptor.identifier == identifier:
                return sensor_status.sub_sensor_status_list[sensor_descriptor.sub_sensor_descriptors.index(sub_sensor_descriptor)]
        return None
