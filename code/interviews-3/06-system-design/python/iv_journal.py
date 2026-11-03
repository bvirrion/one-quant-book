"""An append-only journal: each record is a length, a CRC and the bytes."""
import struct
import zlib

HEADER = struct.Struct("<II")
SEED = 0xFFFFFFFF       # crc32(b"") is 0, and a tail of zeros must not pass


def append(f, payload):
    f.write(HEADER.pack(len(payload), zlib.crc32(payload, SEED)) + payload)


def recover(data):
    """The longest prefix of whole, correct records, and the length that holds them."""
    records, at = [], 0
    while at + HEADER.size <= len(data):
        length, crc = HEADER.unpack_from(data, at)
        body = data[at + HEADER.size : at + HEADER.size + length]
        if len(body) < length or zlib.crc32(body, SEED) != crc:
            break
        records.append(body)
        at += HEADER.size + length
    return records, at
