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
from pykson import ObjectField
from pykson import ObjectListField

from blue_st_sdk.features.hsd.communication.device.device_information import DeviceInformation
from blue_st_sdk.features.hsd.communication.device.sensor import Sensor
from blue_st_sdk.features.hsd.communication.device.tag import TagConfiguration


# CLASSES

class DeviceModel(JsonObject):
    """Device Model."""

    device_information = ObjectField(DeviceInformation, serialized_name = "deviceInfo")
    tag_configuration = ObjectField(TagConfiguration, serialized_name = "tagConfig")
    sensors = ObjectListField(Sensor, serialized_name = "sensor")

    def get_mac_address(id, is_sw):
        if not tag_configuration:
            return None
        tag_configuration_conf = tag_configuration
        if is_sw:
            for tag in tag_configuration_conf.software_tag_configuration:
                if tag.id == id:
                    return tag
        else:
            for tag in tag_configuration_conf.hardware_tag_configuration:
                if tag.id == id:
                    return tag
        return None

    def update_tag_label(tag_id, is_sw, label):
        if tag_configuration and label:
            for tag in (tag_configuration.software_tag_configuration if is_sw else tag_configuration.hardware_tag_configuration):
                if tag.id == tag_id:
                    tag.label = label

    def enable_tag(tag_id, is_sw, is_enabled):
        if tag_configuration:
            for tag in (tag_configuration.software_tag_configuration if is_sw else tag_configuration.hardware_tag_configuration):
                if tag.id == tag_id:
                    tag.is_Enabled = is_enabled

    def get_sensor_by_type(sensor_type):
        if sensors:
            for sensor in sensors:
                for sub_sensor in sensor.sensor_descriptor.sub_sensor_descriptors:
                    if sub_sensor.sensor_type == sensor_type:
                        return SensorCoordinates(sensor.id, sub_sensor.id)
        return None


class SensorCoordinates(object):

    def __init__(self, sensor_id, sub_sensor_id):
        self._sensor_id = sensor_id
        self._sub_sensor_id = sub_sensor_id

    def get_sensor_id(self):
        return self._sensor_id

    def get_sub_sensor_id(self):
        return self._sub_sensor_id
