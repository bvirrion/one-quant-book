"""Merging the A and B lines of a feed: first copy wins; a gap comes after `hold` packets."""


class Arbiter:
    def __init__(self, first=1, hold=8):
        self.next = first
        self.hold = hold
        self.pending = set()
        self.gaps = []

    def on_packet(self, seq):
        """Takes a sequence number from either line; returns those now deliverable."""
        if seq < self.next or seq in self.pending:
            return []                        # the other line got here first
        self.pending.add(seq)
        out = []
        while True:
            while self.next in self.pending:
                self.pending.remove(self.next)
                out.append(self.next)
                self.next += 1
            if len(self.pending) <= self.hold:
                return out
            lowest = min(self.pending)       # waited long enough: give up on what is missing
            self.gaps.append((self.next, lowest - 1))
            self.next = lowest
