"""Pre-trade checks: size, price collar, and position if every open order fills."""


class Risk:
    def __init__(self, limit, max_qty, collar):
        self.limit, self.max_qty, self.collar = limit, max_qty, collar
        self.position = self.open_buys = self.open_sells = 0

    def allow(self, side, qty, price, reference):
        if qty <= 0 or qty > self.max_qty:
            return "size"
        if abs(price - reference) > self.collar * reference:
            return "collar"
        buys = self.open_buys + (qty if side == "buy" else 0)
        sells = self.open_sells + (qty if side == "sell" else 0)
        if self.position + buys > self.limit or self.position - sells < -self.limit:
            return "position"
        self.open_buys, self.open_sells = buys, sells
        return "ok"

    def on_fill(self, side, qty):
        if side == "buy":
            self.open_buys -= qty
            self.position += qty
        else:
            self.open_sells -= qty
            self.position -= qty

    def on_cancel(self, side, qty):
        if side == "buy":
            self.open_buys -= qty
        else:
            self.open_sells -= qty
