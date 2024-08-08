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
from pykson import Pykson
from pykson import JsonObject
from pykson import BooleanField
from pykson import IntegerField
from pykson import FloatField
from pykson import StringField
from pykson import ObjectListField


# CONSTANTS

SEPARATORS = (',', ':')


# CLASSES

class HSDCommand(JsonObject):
    """HSD Command."""

    command = StringField(serialized_name = "command")

    @classmethod
    def start(self):
        json_dict = dict()
        json_dict["command"] = "START"
        return Pykson().from_json(json.dumps(json_dict, separators=SEPARATORS), HSDCommand)

    @classmethod
    def stop(self):
        json_dict = dict()
        json_dict["command"] = "STOP"
        return Pykson().from_json(json.dumps(json_dict, separators=SEPARATORS), HSDCommand)

    @classmethod
    def save(self):
        json_dict = dict()
        json_dict["command"] = "SAVE"
        return Pykson().from_json(json.dumps(json_dict, separators=SEPARATORS), HSDCommand)


class HSDGetCommand(HSDCommand):
    """HSD Get Command."""

    request = StringField(serialized_name = "request")

    @classmethod
    def get_device(self):
        json_dict = dict()
        json_dict["command"] = "GET"
        json_dict["request"] = "device"
        return Pykson().from_json(json.dumps(json_dict, separators=SEPARATORS), HSDGetCommand)

    @classmethod
    def get_device_information(self):
        json_dict = dict()
        json_dict["command"] = "GET"
        json_dict["request"] = "deviceInfo"
        return Pykson().from_json(json.dumps(json_dict, separators=SEPARATORS), HSDGetCommand)

    @classmethod
    def get_network_information(self):
        json_dict = dict()
        json_dict["command"] = "GET"
        json_dict["request"] = "network"
        return Pykson().from_json(json.dumps(json_dict, separators=SEPARATORS), HSDGetCommand)

    @classmethod
    def get_tag_configuration(self):
        json_dict = dict()
        json_dict["command"] = "GET"
        json_dict["request"] = "tag_config"
        return Pykson().from_json(json.dumps(json_dict, separators=SEPARATORS), HSDGetCommand)

    @classmethod
    def get_log_status(self):
        json_dict = dict()
        json_dict["command"] = "GET"
        json_dict["request"] = "log_status"
        return Pykson().from_json(json.dumps(json_dict, separators=SEPARATORS), HSDGetCommand)


class HSDGetCommandWithAddress(HSDGetCommand):
    """HSD Get Command With Address."""

    address = IntegerField(serialized_name = "address")

    @classmethod
    def get_descriptor(self):
        json_dict = dict()
        json_dict["command"] = "GET"
        json_dict["request"] = "descriptor"
        json_dict["address"] = "sensorId"
        return Pykson().from_json(json.dumps(json_dict, separators=SEPARATORS), HSDGetCommandWithAddress)

    @classmethod
    def get_status(self):
        json_dict = dict()
        json_dict["command"] = "GET"
        json_dict["request"] = "status"
        json_dict["address"] = "sensorId"
        return Pykson().from_json(json.dumps(json_dict, separators=SEPARATORS), HSDGetCommandWithAddress)

    @classmethod
    def get_register(self):
        json_dict = dict()
        json_dict["command"] = "GET"
        json_dict["request"] = "register"
        json_dict["address"] = "address"
        return Pykson().from_json(json.dumps(json_dict, separators=SEPARATORS), HSDGetCommandWithAddress)


class HSDSetCommand(HSDCommand):
    """HSD Set Command."""

    request = StringField(serialized_name = "request")


class HSDSetDeviceAliasCommand(HSDSetCommand):
    """HSD Set Device Alias Command."""

    alias = StringField(serialized_name = "alias")
    
    @classmethod
    def set_alias(self, _alias):
        json_dict = dict()
        json_dict["command"] = "SET"
        json_dict["request"] = "deviceInfo"
        json_dict["alias"] = _alias
        return Pykson().from_json(json.dumps(json_dict, separators=SEPARATORS), HSDSetDeviceAliasCommand)


class HSDSetWiFiCommand(HSDSetCommand):
    """HSD Set WiFi Command."""

    ssid = StringField(serialized_name = "ssid")
    password = StringField(serialized_name = "password")
    enable = BooleanField(serialized_name = "enable")
    
    @classmethod
    def set_wifi(self, _ssid, _password, _enable):
        json_dict = dict()
        json_dict["command"] = "SET"
        json_dict["request"] = "network"
        json_dict["ssid"] = _ssid
        json_dict["password"] = _password
        json_dict["enable"] = _enable
        return Pykson().from_json(json.dumps(json_dict, separators=SEPARATORS), HSDSetWiFiCommand)


class HSDSetSWTagCommand(HSDSetCommand):
    """HSD Set SW Tag Command."""

    identifier = IntegerField(serialized_name = "ID")
    enable = BooleanField(serialized_name = "enable")

    @classmethod
    def set_sw_tag(self, _identifier, _enable):
        json_dict = dict()
        json_dict["command"] = "SET"
        json_dict["request"] = "sw_tag"
        json_dict["ID"] = _identifier
        json_dict["enable"] = _enable
        return Pykson().from_json(json.dumps(json_dict, separators=SEPARATORS), HSDSetSWTagCommand)


class HSDSetSWTagLabelCommand(HSDSetCommand):
    """HSD Set SW Tag Label Command."""

    identifier = IntegerField(serialized_name = "ID")
    label = StringField(serialized_name = "label")

    @classmethod
    def set_sw_tag_label(self, _identifier, _label):
        json_dict = dict()
        json_dict["command"] = "SET"
        json_dict["request"] = "sw_tag_label"
        json_dict["ID"] = _identifier
        json_dict["label"] = _label
        return Pykson().from_json(json.dumps(json_dict, separators=SEPARATORS), HSDSetSWTagLabelCommand)


class HSDSetHWTagCommand(HSDSetCommand):
    """HSD Set HW Tag Command."""

    identifier = IntegerField(serialized_name = "ID")
    enable = BooleanField(serialized_name = "enable")

    @classmethod
    def set_hw_tag(self, _identifier, _enable):
        json_dict = dict()
        json_dict["command"] = "SET"
        json_dict["request"] = "hw_tag"
        json_dict["ID"] = _identifier
        json_dict["enable"] = _enable
        return Pykson().from_json(json.dumps(json_dict, separators=SEPARATORS), HSDSetHWTagCommand)


class HSDSetHWTagLabelCommand(HSDSetCommand):
    """HSD Set HW Tag Label Command."""

    identifier = IntegerField(serialized_name = "ID")
    label = StringField(serialized_name = "label")

    @classmethod
    def set_hw_tag_label(self, _identifier, _label):
        json_dict = dict()
        json_dict["command"] = "SET"
        json_dict["request"] = "hw_tag_label"
        json_dict["ID"] = _identifier
        json_dict["label"] = _label
        return Pykson().from_json(json.dumps(json_dict, separators=SEPARATORS), HSDSetHWTagLabelCommand)


class HSDSetAcquisitionInformationCommand(HSDSetCommand):
    """HSD Set Acquisition Information Command."""

    name = StringField(serialized_name = "name")
    notes = StringField(serialized_name = "notes")
    
    @classmethod
    def set_info(self, _name, _notes):
        json_dict = dict()
        json_dict["command"] = "SET"
        json_dict["request"] = "acq_info"
        json_dict["name"] = _name
        json_dict["notes"] = _notes


class SubSensorStatusParameter(JsonObject):
    """Sub Sensor Status Parameter."""

    identifier = IntegerField(serialized_name = "id")


class IsActiveParam(SubSensorStatusParameter):
    """Is Active Parameter."""

    is_active = BooleanField(serialized_name = "isActive")


class ODRParam(SubSensorStatusParameter):
    """ODR Parameter."""

    odr = FloatField(serialized_name = "ODR")


class FSParam(SubSensorStatusParameter):
    """FS Parameter."""

    fs = FloatField(serialized_name = "FS")


class SamplePerTimestampParam(SubSensorStatusParameter):
    """Sample Per Timestamp Parameter."""

    samples_per_timestamp = IntegerField(serialized_name = "samplesPerTs")


class HSDSetSensorCommand(HSDSetCommand):
    """HSD Set Sensor Command."""

    sensor_identifier = IntegerField(serialized_name = "sensorId")
    sub_sensor_status_list = ObjectListField(
        SubSensorStatusParameter, serialized_name = "subSensorStatus")
    
    @classmethod
    def set_sensor(self, _sensor_identifier, _sub_sensor_status_list):
        json_dict = dict()
        json_dict["command"] = "SET"
        json_dict["request"] = None
        json_dict["sensorId"] = _sensor_identifier
        json_dict["subSensorStatus"] = _sub_sensor_status_list


class HSDSetMLCSensorCommand(HSDSetCommand):
    """HSD Set MLC Sensor Command."""

    sensor_identifier = IntegerField(serialized_name = "sensorId")
    sub_sensor_status_list = ObjectListField(
        SubSensorStatusParameter, serialized_name = "subSensorStatus")
    
    @classmethod
    def set_mlc_sensor(self, _sensor_identifier, _sub_sensor_status_list):
        json_dict = dict()
        json_dict["command"] = "SET"
        json_dict["request"] = "mlc_config"
        json_dict["sensorId"] = _sensor_identifier
        json_dict["subSensorStatus"] = _sub_sensor_status_list


#class MLCConfigurationParameter(SubSensorStatusParameter):
    """MLC Configuration Parameter."""

"""
    def __init__(self):
        SubSensorStatusParameter.__init__(self)
        mlc_configuration_size = IntegerField(serialized_name = "mlcConfigSize")
        mlc_configuration_data = StringField(serialized_name = "mlcConfigData")

    def from_ucf_string(self, identifier, ucf_content:String):
        is_space = "\\s+".toRegex()
        compact_string = ucf_content.lineSequence()
            .filter { isCommentLine(it) }
            .map {it.replace(is_space,"").drop(2)  }
            .joinToString("")
        mlc = MLCConfigurationParameter()
        mlc.identifier = identifier
        mlc.mlc_configuration_size = compact_string.length
        mlc.mlc_configuration_data = compact_string
        return 

    def is_comment_line(self, line):
        return not line.startsWith("--")
"""
