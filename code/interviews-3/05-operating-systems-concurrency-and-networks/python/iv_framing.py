"""Length-prefixed messages over a byte stream: a 2-byte big-endian length, then the body."""
import struct

MAX_BODY = 4096


class Deframer:
    def __init__(self):
        self.buf = bytearray()

    def feed(self, data):
        self.buf += data
        out = []
        while len(self.buf) >= 2:
            size = struct.unpack_from("!H", self.buf)[0]
            if size > MAX_BODY:
                raise ValueError("frame too long")
            if len(self.buf) < 2 + size:
                break
            out.append(bytes(self.buf[2:2 + size]))
            del self.buf[:2 + size]
        return out


def frame(body):
    return struct.pack("!H", len(body)) + body
