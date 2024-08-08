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
from pykson import StringField
from pykson import ObjectListField


# CLASSES

class Tag(JsonObject):
    """Tag."""

    _identifier = IntegerField(serialized_name = "id")
    _label = StringField(serialized_name = "label")
    _is_enabled = BooleanField(serialized_name = "enabled")

    def __init__(self, identifier, label, is_enabled):
        _identifier = identifier
        _label = label
        _is_enabled = is_enabled

"""
:Parcelable {

    def __init__(self, (parcel: Parcel) : this(
            parcel.readInt(),
            parcel.readString()!!,
            parcel.readByte() != 0.toByte()) {
    }

    override fun writeToParcel(parcel: Parcel, flags: Int) {
        parcel.writeInt(id)
        parcel.writeString(label)
        parcel.writeByte(if (isEnabled) 1 else 0)
    }

    override fun describeContents(): Int {
        return 0
    }

    companion object CREATOR : Parcelable.Creator<Tag> {
        override fun createFromParcel(parcel: Parcel): Tag {
            return Tag(parcel)
        }

        override fun newArray(size: Int): Array<Tag?> {
            return arrayOfNulls(size)
        }
    }
}
"""


class TagHW(Tag):
    """Hardware Tag."""
    
    _pin_description = StringField(serialized_name = "pinDesc")

    def __init__(self, identifier, pin_description, label, is_enabled):
        Tag.__init__(identifier, label, is_enabled)
        _pin_description = pin_description

"""
    constructor(parcel: Parcel) : super(parcel) {
        pinDesc = parcel.readString()!!
    }

    override fun writeToParcel(parcel: Parcel, flags: Int) {
        super.writeToParcel(parcel, flags)
        parcel.writeString(pinDesc)
    }
"""


class TagConfiguration(JsonObject):
    """Tag Configuration."""

    max_tags_per_acquisition = IntegerField(serialized_name = "maxTagsPerAcq")
    software_tags = ObjectListField(Tag, serialized_name = "swTags")
    hardware_tags = ObjectListField(TagHW, serialized_name = "hwTags")
