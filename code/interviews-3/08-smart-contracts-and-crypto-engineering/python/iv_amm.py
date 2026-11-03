"""A constant-product pool on integers, in the same arithmetic as the contract."""


class Pool:
    def __init__(self, x, y, fee_bps=30):
        self.x, self.y, self.keep = x, y, 10_000 - fee_bps

    def amount_out(self, amount_in, reserve_in, reserve_out):
        after_fee = amount_in * self.keep
        return after_fee * reserve_out // (reserve_in * 10_000 + after_fee)

    def buy_y(self, amount_in):
        out = self.amount_out(amount_in, self.x, self.y)
        self.x, self.y = self.x + amount_in, self.y - out
        return out

    def buy_x(self, amount_in):
        out = self.amount_out(amount_in, self.y, self.x)
        self.x, self.y = self.x - out, self.y + amount_in
        return out

    def price(self):
        return self.y / self.x
