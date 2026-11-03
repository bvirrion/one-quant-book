import hashlib
import math


def bloom_size(n, p):
    bits = -n * math.log(p) / math.log(2) ** 2
    hashes = round(bits / n * math.log(2))
    return math.ceil(bits), hashes


class Bloom:
    def __init__(self, n, p):
        self.m, self.k = bloom_size(n, p)
        self.bits = bytearray(self.m // 8 + 1)

    def _slots(self, key):
        h = hashlib.blake2b(str(key).encode(), digest_size=16).digest()
        a, b = int.from_bytes(h[:8], "little"), int.from_bytes(h[8:], "little")
        return ((a + i * b) % self.m for i in range(self.k))

    def add(self, key):
        for s in self._slots(key):
            self.bits[s // 8] |= 1 << (s % 8)

    def might_contain(self, key):
        return all(self.bits[s // 8] >> (s % 8) & 1 for s in self._slots(key))
