def encode(values):
    out, last = bytearray(), 0
    for v in values:
        d = v - last
        last = v
        z = 2 * d if d >= 0 else -2 * d - 1   # zigzag: 0, -1, 1, -2 become 0, 1, 2, 3
        while z >= 0x80:
            out.append(z & 0x7F | 0x80)
            z >>= 7
        out.append(z)
    return bytes(out)


def decode(data):
    out, last, z, shift = [], 0, 0, 0
    for b in data:
        z |= (b & 0x7F) << shift
        shift += 7
        if b < 0x80:
            last += z // 2 if z % 2 == 0 else -(z + 1) // 2
            out.append(last)
            z, shift = 0, 0
    return out
