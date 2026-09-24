"""Asset-liability management and liquidity (build of One Quant Book 6, chapter 24).

A balance sheet is a list of positions with annual cash-flow schedules (fixed-rate instruments) or a
repricing date (floating), valued on a flat or shocked zero curve. Non-maturity deposits are split into a
core part, slotted as amortising cash flows over a behavioural life, and a non-core part repricing at once;
their rate follows market rates with a deposit beta. Measures: economic value of equity (EVE) and its
change under the six supervisory IRRBB shocks (parallel, short, steepener, flattener; S(t) = exp(-t/4)),
one-year net interest income (NII) sensitivity on a constant balance sheet, the liquidity coverage ratio
(HQLA after haircuts and caps over 30-day stressed net outflows), a funds-transfer-pricing curve, and the
deposit outflow that exhausts the liquid assets.
"""
import math
from collections.abc import Callable
from dataclasses import dataclass, field

USD_SHOCKS = {"parallel": 0.0200, "short": 0.0300, "long": 0.0150}     # BCBS IRRBB (2016), Annex 2, USD


def shock_curve(kind: str, sizes: dict = USD_SHOCKS) -> Callable[[float], float]:
    """Rate change at time t for one of the six supervisory scenarios."""
    def s_short(t):
        return math.exp(-t / 4.0)

    def d_short(t):
        return sizes["short"] * s_short(t)

    def d_long(t):
        return sizes["long"] * (1.0 - s_short(t))

    return {
        "parallel_up": lambda t: sizes["parallel"],
        "parallel_down": lambda t: -sizes["parallel"],
        "short_up": d_short,
        "short_down": lambda t: -d_short(t),
        "steepener": lambda t: -0.65 * abs(d_short(t)) + 0.9 * abs(d_long(t)),
        "flattener": lambda t: 0.8 * abs(d_short(t)) - 0.6 * abs(d_long(t)),
    }[kind]


SCENARIOS = ["parallel_up", "parallel_down", "short_up", "short_down", "steepener", "flattener"]
USD_SHOCKS_2024 = {"parallel": 0.0200, "short": 0.0300, "long": 0.0225}  # BCBS recalibration, July 2024


@dataclass
class Position:
    name: str
    side: str                        # "asset" or "liability"
    amount: float
    rate: float                      # contractual rate (fixed) or spread over market (floating)
    maturity: float                  # years (fixed: amortising or bullet; floating: repricing interval)
    kind: str = "bullet"             # bullet, amortising, floating, cash
    hqla: str | None = None          # "L1", "L2A" or None
    runoff: float = 0.0              # LCR 30-day run-off (liabilities)

    def cashflows(self) -> list[tuple[float, float]]:
        if self.kind == "cash":
            return [(0.0, self.amount)]
        if self.kind == "floating":
            return [(self.maturity, self.amount * (1 + self.rate * self.maturity))]
        n = max(1, round(self.maturity))
        if self.kind == "amortising":
            pay = self.amount * self.rate / (1 - (1 + self.rate) ** -n) if self.rate > 0 else self.amount / n
            return [(float(k), pay) for k in range(1, n + 1)]
        return [(float(k), self.amount * self.rate + (self.amount if k == n else 0.0)) for k in range(1, n + 1)]


@dataclass
class Deposits:
    amount: float
    core_share: float                # behaviourally stable part
    core_life: float                 # years over which the core part is slotted (equal annual run-off)
    rate: float
    beta: float                      # pass-through of market rate changes to the deposit rate
    runoff: float                    # LCR 30-day run-off rate

    def cashflows(self) -> list[tuple[float, float]]:
        core, n = self.amount * self.core_share, max(1, round(self.core_life))
        cf = [(0.0, self.amount * (1 - self.core_share))]
        return cf + [(float(k), core / n + core * (1 - (k - 1) / n) * self.rate) for k in range(1, n + 1)]


@dataclass
class BalanceSheet:
    positions: list[Position]
    deposits: Deposits
    base_rate: float
    extra: list = field(default_factory=list)

    def pv(self, shift: Callable[[float], float] = lambda t: 0.0) -> dict:
        def disc(t):
            return math.exp(-(self.base_rate + shift(t)) * t)

        a = sum(sum(c * disc(t) for t, c in p.cashflows()) for p in self.positions if p.side == "asset")
        lia = sum(sum(c * disc(t) for t, c in p.cashflows()) for p in self.positions if p.side == "liability")
        lia += sum(c * disc(t) for t, c in self.deposits.cashflows())
        return {"assets": a, "liabilities": lia, "eve": a - lia}

    def delta_eve(self, sizes: dict = USD_SHOCKS) -> dict[str, float]:
        base = self.pv()["eve"]
        return {s: self.pv(shock_curve(s, sizes))["eve"] - base for s in SCENARIOS}

    def nii(self, dr: float = 0.0) -> float:
        """One-year NII on a constant balance sheet after a parallel move dr: floating and maturing assets
        reprice, deposits reprice by beta."""
        inc = 0.0
        for p in self.positions:
            sign = 1.0 if p.side == "asset" else -1.0
            if p.kind == "floating" or p.kind == "cash":
                r = self.base_rate + dr + (p.rate if p.kind == "floating" else 0.0)
            else:
                r = p.rate
            inc += sign * p.amount * r
        d = self.deposits
        inc -= d.amount * (d.rate + d.beta * dr)
        return inc


def market_value(p: Position, rate: float) -> float:
    return sum(c * math.exp(-rate * t) for t, c in p.cashflows())


def lcr(positions: list[Position], deposits: list[tuple[float, float]], market_rate: float,
        inflows: float = 0.0) -> dict:
    """HQLA at market value: Level 1 in full, Level 2A with a 15% haircut and capped at 40% of the stock;
    outflows: deposit amount x run-off; inflows capped at 75% of outflows."""
    l1 = sum(market_value(p, market_rate) for p in positions if p.hqla == "L1")
    l2 = 0.85 * sum(market_value(p, market_rate) for p in positions if p.hqla == "L2A")
    l2 = min(l2, 2.0 / 3.0 * l1)          # level 2 at most 40% of the stock: L2 <= 40/60 L1
    out = sum(a * r for a, r in deposits)
    net = out - min(inflows, 0.75 * out)
    return {"hqla": l1 + l2, "level1": l1, "level2": l2, "outflows": out, "lcr": (l1 + l2) / net}


def ftp_rate(base: Callable[[float], float], liquidity_premium: Callable[[float], float], tenor: float) -> float:
    return base(tenor) + liquidity_premium(tenor)


def run_capacity(liquid: float, deposits: float) -> float:
    """Share of deposits that can be withdrawn before liquid resources are exhausted."""
    return liquid / deposits


def bond_price_change(coupon: float, maturity: int, y0: float, y1: float) -> float:
    """Relative price change of an annual bullet bond when its yield moves from y0 to y1."""
    def price(y):
        return sum(coupon / (1 + y) ** k for k in range(1, maturity + 1)) + 1 / (1 + y) ** maturity
    return price(y1) / price(y0) - 1


def duration(coupon: float, maturity: int, y: float) -> float:
    cf = [(k, coupon + (1.0 if k == maturity else 0.0)) for k in range(1, maturity + 1)]
    pv = [c / (1 + y) ** k for k, c in cf]
    return sum(k * v for (k, _), v in zip(cf, pv, strict=True)) / sum(pv)


def eve_ratio(delta_eve: dict[str, float], tier1: float) -> float:
    """Largest EVE loss over the six scenarios, as a share of Tier 1 (the outlier test threshold is 15%)."""
    return -min(delta_eve.values()) / tier1
