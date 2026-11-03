class Recovering:
    """Deltas are (seq, price, new_size); a snapshot is (last_seq, {price: size})."""

    def __init__(self):
        self.book, self.seq, self.buffer = None, None, []

    def on_delta(self, seq, price, size):
        if self.book is None:                    # not live yet: hold until a snapshot arrives
            self.buffer.append((seq, price, size))
            return "buffering"
        if seq <= self.seq:
            return "duplicate"
        if seq != self.seq + 1:                  # a gap: this book can no longer be trusted
            self.book, self.buffer = None, [(seq, price, size)]
            return "gap"
        self._apply(seq, price, size)
        return "ok"

    def on_snapshot(self, last_seq, levels):
        if self.book is not None:                # live: a snapshot could only rewind it
            return True
        book, seq = dict(levels), last_seq
        for s, price, size in sorted(self.buffer, key=lambda u: u[0]):
            if s <= seq:
                continue
            if s != seq + 1:                     # snapshot too old, or a hole in the buffer
                return False
            seq = s
            book[price] = size
            if size == 0:
                del book[price]
        self.book, self.seq, self.buffer = book, seq, []
        return True

    def _apply(self, seq, price, size):
        self.seq = seq
        self.book[price] = size
        if size == 0:
            del self.book[price]
