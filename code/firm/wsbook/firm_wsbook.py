"""Websocket order-book builder (build of Book 3, Chapter 26): Python reference of the C++20 and Rust twins.

A snapshot with an update id, then deltas carrying a first and a last update id (U, u) and absolute
quantities per price level (zero removes the level). Following the procedure a large venue documents:
events with u below the book's id are ignored; an event with U above the book's id + 1 means updates were
missed, and the book must be discarded and resynchronised from a new snapshot. A checksum in the style
another venue documents verifies the top of the book: the ten best asks (low to high) then the ten best
bids (high to low), each price and quantity written as an integer without leading zeros, concatenated,
CRC32. Prices and quantities are integers (ticks and lots).
"""
import zlib


class Book:
    def __init__(self) -> None:
        self.bids: dict[int, int] = {}
        self.asks: dict[int, int] = {}
        self.update_id = -1
        self.synced = False

    def snapshot(self, update_id: int, bids: list[tuple[int, int]], asks: list[tuple[int, int]]) -> None:
        self.bids, self.asks = dict(bids), dict(asks)
        self.update_id, self.synced = update_id, True

    def apply(self, first: int, last: int, bids: list[tuple[int, int]], asks: list[tuple[int, int]]) -> str:
        """Returns 'ignored', 'applied' or 'gap' (the book is then unsynced until a new snapshot)."""
        if not self.synced:
            return "gap"
        if last < self.update_id + 1:
            return "ignored"
        if first > self.update_id + 1:
            self.synced = False
            return "gap"
        for side, levels in ((self.bids, bids), (self.asks, asks)):
            for p, q in levels:
                if q == 0:
                    side.pop(p, None)
                else:
                    side[p] = q
        self.update_id = last
        return "applied"

    def top(self, n: int = 10) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
        b = sorted(self.bids.items(), key=lambda x: -x[0])[:n]
        a = sorted(self.asks.items())[:n]
        return b, a

    def checksum(self) -> int:
        b, a = self.top(10)
        s = "".join(f"{p}{q}" for p, q in a) + "".join(f"{p}{q}" for p, q in b)
        return zlib.crc32(s.encode()) & 0xFFFFFFFF


def crc32(data: bytes) -> int:
    """Bitwise CRC32 (reflected, polynomial 0xEDB88320), the algorithm the C++ and Rust twins implement."""
    c = 0xFFFFFFFF
    for byte in data:
        c ^= byte
        for _ in range(8):
            c = (c >> 1) ^ (0xEDB88320 if c & 1 else 0)
    return c ^ 0xFFFFFFFF
