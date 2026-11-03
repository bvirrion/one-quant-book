"""Sorted timestamps as deltas, then as variable-length integers of 7 bits a byte."""


def encode(values):
    out, last = bytearray(), 0
    for v in values:
        d, last = v - last, v
        z = (d << 1) ^ (d >> 63)             # zigzag: small negatives become small positives
        while z >= 0x80:
            out.append(z & 0x7F | 0x80)
            z >>= 7
        out.append(z)
    return bytes(out)


def decode(data):
    values, last, z, shift = [], 0, 0, 0
    for byte in data:
        z |= (byte & 0x7F) << shift
        shift += 7
        if byte < 0x80:
            d = (z >> 1) ^ -(z & 1)
            last += d
            values.append(last)
            z = shift = 0
    return values
