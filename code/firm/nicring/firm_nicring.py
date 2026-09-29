"""firm.nicring -- a network card's receive descriptor ring, Python reference (build of One Quant Book 14, chapter 3).

The card writes each arriving packet into the next descriptor that it owns, flips the descriptor's owner bit to the
host and advances its head; if the next descriptor still belongs to the host (not yet processed and handed back),
the packet is dropped. The host polls: it processes up to `budget` descriptors it owns, in order, and hands them
back to the card in batches of `refill` (one doorbell write per batch). The C++20 (cpp/firm_nicring.hpp) and Rust
(rust/) twins reproduce data/expected.txt on data/events.txt exactly.

Events: ("N", seq, length) a packet reaches the card; ("P", budget) the host polls.

API (stable):
    Ring(size, refill=1)               size a power of two; refill in [1, size]
    .nic_rx(seq, length) -> bool       False if dropped (ring full)
    .poll(budget) -> int               descriptors processed
    .run(events) -> Ring
    counters: rx, drops, processed, doorbells, hash (FNV-1a over (seq, length) in processing order),
              max_owned (the most descriptors the host held at once)
    make_events(n, rate_per_poll, budget, seed) -> list    deterministic event stream for tests and fixtures
"""
import random

FNV_OFFSET, FNV_PRIME, MASK = 0xCBF29CE484222325, 0x100000001B3, (1 << 64) - 1
NIC, HOST = 0, 1


class Ring:
    def __init__(self, size, refill=1):
        if size & (size - 1) or not 1 <= refill <= size:
            raise ValueError("size must be a power of two and 1 <= refill <= size")
        self.size, self.refill = size, refill
        self.owner = [NIC] * size
        self.seq = [0] * size
        self.length = [0] * size
        self.head = self.tail = 0          # head: next descriptor the card fills; tail: next the host reads
        self.pending = 0                   # processed by the host, not yet handed back
        self.rx = self.drops = self.processed = self.doorbells = self.max_owned = 0
        self.hash = FNV_OFFSET

    def nic_rx(self, seq, length):
        i = self.head
        if self.owner[i] == HOST:
            self.drops += 1
            return False
        self.seq[i], self.length[i], self.owner[i] = seq, length, HOST
        self.head = (i + 1) % self.size
        self.rx += 1
        return True

    def _mix(self, x):
        for _ in range(8):
            self.hash = ((self.hash ^ (x & 0xFF)) * FNV_PRIME) & MASK
            x >>= 8

    def poll(self, budget):
        n = 0
        while n < budget and self.rx > self.processed:
            i = self.tail
            self._mix(self.seq[i])
            self._mix(self.length[i])
            self.tail = (i + 1) % self.size
            self.processed += 1
            self.pending += 1
            n += 1
            if self.pending >= self.refill:
                self._give_back()
        return n

    def _give_back(self):
        start = (self.tail - self.pending) % self.size
        for k in range(self.pending):
            self.owner[(start + k) % self.size] = NIC
        self.pending = 0
        self.doorbells += 1

    def run(self, events):
        for e in events:
            if e[0] == "N":
                self.nic_rx(e[1], e[2])
            else:
                self.poll(e[1])
            held = self.rx - self.processed + self.pending
            self.max_owned = max(self.max_owned, held)
        return self


def make_events(n, rate_per_poll, budget, seed):
    """n packet arrivals; between polls a Poisson-like burst of arrivals of mean rate_per_poll (deterministic)."""
    rng = random.Random(seed)
    ev, seq = [], 0
    while seq < n:
        k = 0
        while rng.random() < rate_per_poll / (rate_per_poll + 1):
            k += 1
        for _ in range(k):
            if seq < n:
                ev.append(("N", seq, 60 + rng.randrange(1400)))
                seq += 1
        ev.append(("P", budget))
    return ev
