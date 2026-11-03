import socket
import struct
import sys

x = 0x01020304
print(sys.byteorder)
print(struct.pack("=I", x).hex(), struct.pack("!I", x).hex())
print(hex(socket.htonl(x)))
