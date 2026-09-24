"""Option-chain container (build of Book 1, Chapter 23).

Series are identified by their 21-character OSI symbol: root (6, space padded), expiry YYMMDD,
C or P, strike in thousandths of a dollar (8 digits). Strikes are integers of thousandths
throughout: no floating-point strike ever becomes a dictionary key.
"""
import datetime as dt
from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Series:
    root: str
    expiry: dt.date
    right: str                      # 'C' or 'P'
    strike_milli: int               # strike price x 1000
    multiplier: int = 100
    style: str = "american"         # or 'european'
    settlement: str = "physical"    # or 'cash'

    @property
    def strike(self) -> float:
        return self.strike_milli / 1000.0

    @property
    def osi(self) -> str:
        return f"{self.root:<6}{self.expiry:%y%m%d}{self.right}{self.strike_milli:08d}"

    def intrinsic(self, underlying: float) -> float:
        diff = underlying - self.strike if self.right == "C" else self.strike - underlying
        return max(diff, 0.0)

    def payoff(self, underlying: float, premium: float, qty: int) -> float:
        """P&L at expiry of `qty` contracts (negative = short) bought or sold at `premium`."""
        return qty * self.multiplier * (self.intrinsic(underlying) - premium)


def parse_osi(symbol: str, **kwargs) -> Series:
    if len(symbol) != 21:
        raise ValueError(f"an OSI symbol has 21 characters, got {len(symbol)}: {symbol!r}")
    root, date, right, strike = symbol[:6].rstrip(), symbol[6:12], symbol[12], symbol[13:]
    if not root or right not in "CP" or not (date + strike).isdigit():
        raise ValueError(f"malformed OSI symbol {symbol!r}")
    expiry = dt.datetime.strptime(date, "%y%m%d").date()
    return Series(root, expiry, right, int(strike), **kwargs)


class Chain:
    """All series of one underlying, indexed by expiry and strike."""

    def __init__(self, series: list[Series]) -> None:
        self._by_key: dict[tuple[dt.date, int, str], Series] = {}
        for s in series:
            key = (s.expiry, s.strike_milli, s.right)
            if key in self._by_key:
                raise ValueError(f"duplicate series {s.osi}")
            self._by_key[key] = s

    def __len__(self) -> int:
        return len(self._by_key)

    def expiries(self) -> list[dt.date]:
        return sorted({k[0] for k in self._by_key})

    def strikes(self, expiry: dt.date) -> list[int]:
        return sorted({k[1] for k in self._by_key if k[0] == expiry})

    def get(self, expiry: dt.date, strike_milli: int, right: str) -> Series:
        return self._by_key[(expiry, strike_milli, right)]

    def atm_strike(self, expiry: dt.date, underlying: float) -> int:
        return min(self.strikes(expiry), key=lambda k: (abs(k / 1000.0 - underlying), k))


EX_BY_EX_THRESHOLD = 0.01           # dollars in the money at which an expiring option is exercised by default


def exercised_by_exception(series: Series, closing_price: float) -> bool:
    return series.intrinsic(closing_price) >= EX_BY_EX_THRESHOLD - 1e-12


def expiry_shares(positions: dict[Series, int], closing_price: float,
                  overrides: dict[Series, bool] | None = None) -> int:
    """Net shares received (+) or delivered (-) after expiry of physically settled options,
    assuming every short in-the-money position is assigned in full. `overrides` forces the
    exercise decision of LONG positions (contrary instructions)."""
    shares = 0
    for s, qty in positions.items():
        if s.settlement != "physical":
            continue
        exercise = exercised_by_exception(s, closing_price)
        if qty > 0 and overrides and s in overrides:
            exercise = overrides[s]
        if not exercise:
            continue
        direction = 1 if s.right == "C" else -1      # exercising a call buys shares; a put sells them
        shares += direction * qty * s.multiplier
    return shares
