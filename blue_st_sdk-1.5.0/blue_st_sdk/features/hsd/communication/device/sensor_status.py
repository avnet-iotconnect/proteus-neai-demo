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
from pykson import ObjectListField

from blue_st_sdk.features.hsd.communication.device.sub_sensor_status import SubSensorStatus


# CLASSES

class SensorStatus(JsonObject):
    """Sensor status."""

    sub_sensor_status_list = ObjectListField(SubSensorStatus, serialized_name = "subSensorStatus")
    params_locked = False

    def get_sub_sensor_status(self, sub_sensor_id):
        if sub_sensor_id < len(sub_sensor_status_list):
            return sub_sensor_status_list[sub_sensor_id]
        return None

    def equals(self, other):
        if self == other:
            return True
        if type(self) != type(other):
            return False
        if sub_sensor_status_list != other.sub_sensor_status_list:
            return False
        if params_locked != other.params_locked:
            return False
        return True

    def hash(self):
        result = sub_sensor_status_list.hash()
        result = 31 * result + params_locked.hash()
        return result


class SensorStatusWithId(object):
    """Sensor status and identifier."""

    def __init__(self, sensor_id, sensor_status):
        self._sensor_id = sensor_id
        self._sensor_status = sensor_status

    def get_sensor_id(self):
        return self._sensor_id

    def get_sensor_status(self):
        return self._sensor_status
