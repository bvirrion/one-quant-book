"""A book of price levels from a numbered incremental feed and a snapshot taken later on."""


class BookSync:
    def __init__(self):
        self.book = self.last = None
        self.buffer = []

    def on_incremental(self, seq, price, qty):
        if self.book is None:
            self.buffer.append((seq, price, qty))
        elif seq == self.last + 1:
            self._apply(seq, price, qty)
        elif seq > self.last + 1:            # a gap: this book can no longer be trusted
            self.book = self.last = None
            self.buffer = [(seq, price, qty)]

    def on_snapshot(self, seq, levels):
        if self.book is not None:
            return
        self.book, self.last = dict(levels), seq
        for s, price, qty in self.buffer:
            if s == self.last + 1:
                self._apply(s, price, qty)
            elif s > self.last + 1:          # the buffer does not reach: wait for another
                self.book = self.last = None
                return
        self.buffer = []

    def _apply(self, seq, price, qty):
        if qty:
            self.book[price] = qty
        else:
            self.book.pop(price, None)
        self.last = seq
