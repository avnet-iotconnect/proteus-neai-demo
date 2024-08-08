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

from blue_st_sdk.utils.number_conversion import BigEndian


# CONSTANTS



# CLASSES

class STL2TransportProtocol(object):
    """Transport Protocol Manager."""
    
    DEFAULT_MTU_SIZE_bytes = 20
    """Default size of the MTU in bytes."""

    MAXIMUM_ST_MTU_SIZE_bytes = 255
    """Maximum size of the MTU in bytes."""

    STM32L4_MINIMUM_BURST_SIZE_bytes = 8
    """The STM32L4 Family can write only 8 bytes at a time."""

    _TP_START_PACKET = 0
    _TP_START_END_PACKET = 32
    _TP_MIDDLE_PACKET = 64
    _TP_END_PACKET = 128
    """"Packet identifiers."""

    def __init__(self, mtu_bytes = DEFAULT_MTU_SIZE_bytes):
        self._mtu_bytes = mtu_bytes
        self._current_message_bytearray = bytearray()
        self._received_bytes = 0
        self._received_packets = 0

    def get_mtu_bytes(self):
        """Get the MTU size in bytes.
        
        Returns:
            int: The MTU size in bytes.
        """
        return self._mtu_bytes

    def encapsulate(self, message_str):
        """Encode a message.

        Pack the string message in a transport protocol stream of bytes.
        
        Args:
            message_str (string): The message to be encoded.

        Returns:
            bytearray: The encoded data.
        """     
        message_bytes = message_str.encode("utf-8")
        self._message_bytes = bytearray()
        head = STL2TransportProtocol._TP_START_PACKET
        bytes_processed = 0
        while bytes_processed < len(message_bytes):
            size = min(self._mtu_bytes - 1, len(message_bytes) - bytes_processed)
            if len(message_bytes) - bytes_processed <= self._mtu_bytes - 1:
                if bytes_processed == 0:
                    if len(message_bytes) - bytes_processed <= self._mtu_bytes - 3:
                        head = STL2TransportProtocol._TP_START_END_PACKET
                    else:
                        head = STL2TransportProtocol._TP_START_PACKET
                else:
                    head = STL2TransportProtocol._TP_END_PACKET
            if head == STL2TransportProtocol._TP_START_PACKET:
                    self._message_bytes.append(head)
                    self._message_bytes.extend(BigEndian.int16_to_bytes(len(message_bytes)))
                    self._message_bytes.extend(bytearray(message_bytes[0:self._mtu_bytes - 3]))
                    size = self._mtu_bytes - 3
                    head = STL2TransportProtocol._TP_MIDDLE_PACKET
            elif head == STL2TransportProtocol._TP_START_END_PACKET:
                    self._message_bytes.append(head)
                    self._message_bytes.extend(BigEndian.int16_to_bytes(len(message_bytes)))
                    self._message_bytes.extend(bytearray(message_bytes[0:len(message_bytes)]))
                    size = len(message_bytes)
                    head = STL2TransportProtocol._TP_START_PACKET
            elif head == STL2TransportProtocol._TP_MIDDLE_PACKET:
                    self._message_bytes.append(head)
                    self._message_bytes.extend(bytearray(message_bytes[bytes_processed:bytes_processed + self._mtu_bytes - 1]))
            elif head == STL2TransportProtocol._TP_END_PACKET:
                    self._message_bytes.append(head)
                    self._message_bytes.extend(bytearray(message_bytes[bytes_processed:bytes_processed + len(message_bytes) - bytes_processed]))
                    head = STL2TransportProtocol._TP_START_PACKET
            bytes_processed += size
        return self._message_bytes

    def decapsulate(self, message_bytes):
        """Decode a message.

        Check data transport protocol byte, update the current encoded message
        and return the decoded message as a bytearray in case of an "END" packet,
        None otherwise.

        Args:
            message_bytes (bytearray): The data that belongs to the message to
                be decoded.

        Returns:
            str: The decoded message in case of an "END" packet data, None
            otherwise.
        """
        # Update current message.
        if message_bytes[0] == STL2TransportProtocol._TP_START_PACKET:
            self._current_message_bytearray = bytearray()
            self._current_message_bytearray.extend(message_bytes[1:])
            self._received_bytes = len(message_bytes) - 1
            self._received_packets = 1
        elif message_bytes[0] == STL2TransportProtocol._TP_START_END_PACKET:
            self._current_message_bytearray = bytearray()
            self._current_message_bytearray.extend(message_bytes[1:])
            self._received_bytes = len(message_bytes) - 1
            self._received_packets = 1
        elif message_bytes[0] == STL2TransportProtocol._TP_MIDDLE_PACKET:
            self._current_message_bytearray.extend(message_bytes[1:])
            self._received_bytes += len(message_bytes) - 1
            self._received_packets += 1
        elif message_bytes[0] == STL2TransportProtocol._TP_END_PACKET:
            if self._current_message_bytearray:
                self._current_message_bytearray.extend(message_bytes[1:])
                self._received_bytes += len(message_bytes) - 1
                self._received_packets += 1
        # Return current message.
        if message_bytes[0] == STL2TransportProtocol._TP_START_END_PACKET or \
            message_bytes[0] == STL2TransportProtocol._TP_END_PACKET:
            self._current_message_bytearray = self._current_message_bytearray.decode('unicode_escape')
            if self._current_message_bytearray[-1] == '\x00':
                self._current_message_bytearray = self._current_message_bytearray[:-1]
                self._received_bytes -= 1
            return self._current_message_bytearray
        return None

    def set_mtu_bytes(self, mtu_bytes):
        self._mtu_bytes = mtu_bytes
    
    def get_mtu_bytes(self):
        return self._mtu_bytes

    def get_received_bytes(self):
        return self._received_bytes

    def get_received_packets(self):
        return self._received_packets
