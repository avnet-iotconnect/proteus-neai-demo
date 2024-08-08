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

from pykson import Pykson
from pykson import JsonObject

from blue_st_sdk.features.hsd.communication.device.response import Response


# CLASSES

class DeviceParser(object):

    @classmethod
    def to_json_object(self, command_json_str):
        #command_str = raw_data.toString(Charsets.UTF_8).dropLast(1)
        try:
            return Pykson().from_json(command_json_str, JsonObject)
        except Exception as e:
            raise Exception("HSD DeviceParser: " + str(e))

    @classmethod
    def to_json_str(self, command_json_object):
        try:
            return Pykson().to_json(command_json_object)
        except Exception as e:
            raise Exception("HSD DeviceParser: " + str(e))

"""
        fun toJsonStr(sensors:List<Sensor>):String{
            return gsonEncDec.toJsonTree(sensors).toString()
        }

        fun extractSensors(json:String):List<Sensor>?{
            return try {
                val listType: Type = object : TypeToken<List<Sensor>?>() {}.type
                gsonEncDec.fromJson(json,listType)
            }catch (e: JsonSyntaxException){
                null
            }
        }

        @JvmStatic
        fun extractDevice(obj:JsonObject?): Device?{
            obj ?: return null
            if(obj.has("device")){
                return try {
                    gsonEncDec.fromJson(obj,
                            Response::class.java).device
                }catch (e: JsonSyntaxException){
                    Log.e("HSD DeviceParser","error parsing the DeviceStatus: $e")
                    Log.e("HSD DeviceParser",obj.toString())
                    null
                }
            }
            if(obj.has("deviceInfo")){
                return try {
                    gsonEncDec.fromJson(obj,
                            Device::class.java)
                }catch (e: JsonSyntaxException){
                    Log.e("HSD DeviceParser","error parsing the DeviceStatus: $e")
                    Log.e("HSD DeviceParser",obj.toString())
                    null
                }
            }
            if(obj.has(("tagConfig"))){
                return try {
                    gsonEncDec.fromJson(obj,
                            Device::class.java)
                }catch (e: JsonSyntaxException){
                    Log.e("HSD DeviceParser","error parsing the DeviceStatus: $e")
                    Log.e("HSD DeviceParser",obj.toString())
                    null
                }
            }
            return null
        }

        @JvmStatic
        fun extractDeviceStatus(obj:JsonObject?): DeviceStatus?{
            obj ?: return null
            return try {
                gsonEncDec.fromJson(obj,
                        DeviceStatus::class.java)
            }catch (e: JsonSyntaxException){
                Log.e("HSD DeviceParser","error parsing the DeviceStatus: $e")
                Log.e("HSD DeviceParser",obj.toString())
                null
            }
        }

    }
}

private object SensorTypeSerializer : JsonSerializer<SensorType>,JsonDeserializer<SensorType>{
    override fun serialize(src: SensorType?, typeOfSrc: Type?, context: JsonSerializationContext?): JsonElement {
        return when(src){
            SensorType.Accelerometer -> JsonPrimitive("ACC")
            SensorType.Magnetometer -> JsonPrimitive("MAG")
            SensorType.Gyroscope -> JsonPrimitive("GYRO")
            SensorType.Temperature -> JsonPrimitive("TEMP")
            SensorType.Humidity -> JsonPrimitive("HUM")
            SensorType.Pressure -> JsonPrimitive("PRESS")
            SensorType.Microphone -> JsonPrimitive("MIC")
            SensorType.MLC -> JsonPrimitive("MLC")
            null,SensorType.Unknown -> JsonPrimitive("")
        }
    }

    override fun deserialize(json: JsonElement?, typeOfT: Type?, context: JsonDeserializationContext?): SensorType {
        val str = json?.asString ?: return SensorType.Unknown
        return when (str.toUpperCase(Locale.getDefault())){
            "ACC" -> SensorType.Accelerometer
            "MAG" -> SensorType.Magnetometer
            "GYRO" -> SensorType.Gyroscope
            "TEMP" -> SensorType.Temperature
            "HUM" -> SensorType.Humidity
            "PRESS" -> SensorType.Pressure
            "MIC" -> SensorType.Microphone
            "MLC" -> SensorType.MLC
            else -> SensorType.Unknown
        }
    }

}
"""
