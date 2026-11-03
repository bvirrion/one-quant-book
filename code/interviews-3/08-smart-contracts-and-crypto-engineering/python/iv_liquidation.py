"""A long perpetual with isolated margin: when is it closed, and who pays for a gap?"""


def liquidation_price(entry, qty, margin, maintenance):
    """The mark at which equity falls to maintenance times the notional at that mark."""
    return (entry * qty - margin) / (qty * (1 - maintenance))


class Position:
    def __init__(self, entry, qty, margin, maintenance):
        self.entry, self.qty, self.margin, self.maintenance = entry, qty, margin, maintenance

    def equity(self, mark):
        return self.margin + (mark - self.entry) * self.qty

    def must_close(self, mark):
        return self.equity(mark) <= self.maintenance * mark * self.qty

    def close(self, fill_price, insurance):
        """Closes at the fill. Returns the fund after it. Below zero, others must pay."""
        left = self.equity(fill_price)
        return insurance + min(left, 0.0)
