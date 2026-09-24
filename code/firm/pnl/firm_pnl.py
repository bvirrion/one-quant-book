"""firm.pnl -- position and P&L keeper (build of Chapter 7, One Quant Book 1).

Exact part: quantity and cash are integers (cash in ledger units, 1/10 000 of the
currency unit), so  total = cash + quantity * mark - fees  holds to the unit.
Reported part: the realised / unrealised split under the average-cost convention,
kept in floating point because an average cost is not an integer.
"""
from dataclasses import dataclass, field

BUY, SELL = 1, -1


@dataclass
class Position:
    quantity: int = 0            # signed
    cash: int = 0                # signed sum of trade cash flows, ledger units
    fees: int = 0                # ledger units, positive = paid
    avg_cost: float = 0.0        # ledger units per share, of the open position
    realised: float = 0.0        # ledger units

    def on_fill(self, side: int, quantity: int, price: int, fee: int = 0) -> None:
        if side not in (BUY, SELL) or quantity <= 0 or price <= 0 or fee < 0:
            raise ValueError("bad fill")
        self.cash -= side * quantity * price
        self.fees += fee
        signed = side * quantity
        if self.quantity == 0 or (self.quantity > 0) == (signed > 0):      # opening or adding
            total = abs(self.quantity) + quantity
            self.avg_cost = (abs(self.quantity) * self.avg_cost + quantity * price) / total
            self.quantity += signed
            return
        closing = min(quantity, abs(self.quantity))                         # reducing or flipping
        direction = 1 if self.quantity > 0 else -1
        self.realised += direction * closing * (price - self.avg_cost)
        self.quantity += signed
        if quantity > closing:                                              # flipped: remainder opens at price
            self.avg_cost = float(price)
        elif self.quantity == 0:
            self.avg_cost = 0.0

    def unrealised(self, mark: int) -> float:
        return self.quantity * (mark - self.avg_cost)

    def total(self, mark: int) -> int:
        """Exact: what the position is worth now plus every cash flow so far, less fees."""
        return self.cash + self.quantity * mark - self.fees


@dataclass
class Book:
    positions: dict[str, Position] = field(default_factory=dict)

    def on_fill(self, symbol: str, side: int, quantity: int, price: int, fee: int = 0) -> None:
        self.positions.setdefault(symbol, Position()).on_fill(side, quantity, price, fee)

    def total(self, marks: dict[str, int]) -> int:
        return sum(p.total(marks[s]) for s, p in self.positions.items())

    def gross_exposure(self, marks: dict[str, int]) -> int:
        return sum(abs(p.quantity) * marks[s] for s, p in self.positions.items())

    def net_exposure(self, marks: dict[str, int]) -> int:
        return sum(p.quantity * marks[s] for s, p in self.positions.items())
