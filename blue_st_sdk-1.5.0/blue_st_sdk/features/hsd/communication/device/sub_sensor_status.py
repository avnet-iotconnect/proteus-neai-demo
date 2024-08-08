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
from pykson import BooleanField
from pykson import IntegerField
from pykson import FloatField


# CLASSES

class SubSensorStatus(JsonObject):
    """Sub Sensor Status."""

    is_active = BooleanField(serialized_name = "isActive")
    odr = FloatField(serialized_name = "ODR")
    odr_measured = FloatField(serialized_name = "ODRMeasured")
    initial_offset = IntegerField(serialized_name = "initialOffset")
    samples_per_ts = IntegerField(serialized_name = "samplesPerTs")
    fs = FloatField(serialized_name = "FS")
    sensitivity = FloatField(serialized_name = "sensitivity")
    usb_data_packet_size = IntegerField(serialized_name = "usbDataPacketSize")
    sd_write_buffer_size = IntegerField(serialized_name = "sdWriteBufferSize")
    wifi_data_packet_size = IntegerField(serialized_name = "wifiDataPacketSize")
    com_channel_number = IntegerField(serialized_name = "comChannelNumber")
    ucf_loaded = BooleanField(serialized_name = "ucfLoaded")
