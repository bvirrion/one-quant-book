"""A hash ring with virtual nodes, and the plain modulo rule to compare it with."""
import bisect
import hashlib


def h(text):
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")


def modulo_node(key, n):
    return h(key) % n


class Ring:
    def __init__(self, nodes, vnodes=100):
        points = sorted((h(f"{n}#{i}"), n) for n in nodes for i in range(vnodes))
        self.hashes = [p[0] for p in points]
        self.owners = [p[1] for p in points]

    def node(self, key):
        i = bisect.bisect(self.hashes, h(key)) % len(self.hashes)
        return self.owners[i]
