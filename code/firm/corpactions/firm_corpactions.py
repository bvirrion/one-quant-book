"""firm.corpactions -- corporate-action adjuster (build of Chapter 8, One Quant Book 1)."""
import datetime as dt
from dataclasses import dataclass

KINDS = ("split", "cash_dividend", "rights", "spinoff")


@dataclass(frozen=True)
class Action:
    symbol: str
    ex_date: dt.date
    kind: str
    params: dict           # split: ratio; cash_dividend: amount, cum_price; rights: cum_price, old, new,
    announced: dt.date     #   subscription; spinoff: cum_price, value


class Adjuster:
    def __init__(self, dividend_convention: str = "cum_less_dividend") -> None:
        if dividend_convention != "cum_less_dividend":
            raise ValueError("only the (P - D) / P convention is implemented")
        self.dividend_convention = dividend_convention
        self._actions: list[Action] = []

    def add(self, a: Action) -> None:
        if a.kind not in KINDS:
            raise ValueError(f"unknown action kind {a.kind!r}")
        if a.announced > a.ex_date:
            raise ValueError("an action cannot be announced after its ex-date")
        self._actions.append(a)

    @staticmethod
    def _factor(a: Action) -> float:
        p = a.params
        if a.kind == "split":
            return 1.0 / p["ratio"]
        if a.kind == "cash_dividend":
            return (p["cum_price"] - p["amount"]) / p["cum_price"]
        if a.kind == "rights":
            terp = (p["old"] * p["cum_price"] + p["new"] * p["subscription"]) / (p["old"] + p["new"])
            return terp / p["cum_price"]
        return (p["cum_price"] - p["value"]) / p["cum_price"]

    def factor(self, symbol: str, date: dt.date, as_of: dt.date) -> float:
        """Product of the factors of actions with date < ex_date <= as_of, known by as_of."""
        f = 1.0
        for a in self._actions:
            if a.symbol == symbol and date < a.ex_date <= as_of and a.announced <= as_of:
                f *= self._factor(a)
        return f


def split_position(quantity: int, avg_cost: float, ratio: float) -> tuple[float, float]:
    """A k-for-1 split: quantity x k, average cost / k, cost basis unchanged."""
    return quantity * ratio, avg_cost / ratio
