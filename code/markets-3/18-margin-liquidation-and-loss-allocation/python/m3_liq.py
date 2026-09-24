"""Book 3, Chapter 18: liquidation prices, and a liquidation cascade with its stability under a finer
time step and ablations of each mechanism."""
import pathlib
import random
import sys
from dataclasses import dataclass

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/liquidation"))
from firm_liquidation import bankruptcy_price_linear, liq_price_inverse, liq_price_linear  # noqa: E402, F401

P0 = 100.0
MMR = 0.005


@dataclass(frozen=True)
class Long:
    units: float
    entry: float
    leverage: float

    @property
    def margin(self) -> float:
        return self.units * self.entry / self.leverage

    @property
    def liq(self) -> float:
        return liq_price_linear(self.units, self.entry, self.margin, MMR)

    @property
    def bankrupt(self) -> float:
        return bankruptcy_price_linear(self.units, self.entry, self.margin)


def population(n: int = 4_000, seed: int = 18, max_leverage: float = 50.0) -> list[Long]:
    """Leveraged longs: notional lognormal (about USD 25,000 each), entries around 100, leverage a mix of
    low (2-5x), middle (5-20x) and high (20-50x), capped at max_leverage; only positions alive at 100."""
    rng = random.Random(seed)
    out = []
    while len(out) < n:
        u = rng.random()
        lev = rng.uniform(2, 5) if u < 0.4 else rng.uniform(5, 20) if u < 0.8 else rng.uniform(20, 50)
        pos = Long(rng.lognormvariate(5.0, 1.0) * 25 / 15, P0 * (1 + rng.gauss(0, 0.03)), min(lev, max_leverage))
        if pos.liq < P0:
            out.append(pos)
    return out


@dataclass
class Result:
    price: float                  # after the cascade
    liquidated: int
    sold_units: float
    fund_change: float            # surplus minus deficits against bankruptcy prices
    deficit: float                # the deficits alone (positive)
    path: list[tuple[int, float, float]]


def cascade(pop: list[Long], shock: float, impact: float = 1.2e-5, batch: int | None = None,
            forced_selling: bool = True) -> Result:
    """Price falls by `shock`, then every long whose liquidation price is reached is sold into the book,
    each unit sold moving the price down by `impact` (a linear, permanent impact). Triggered positions are
    liquidated all at once (batch=None) or `batch` at a time, highest liquidation price first, re-checking
    after each batch. Each batch executes at the average of its start and end prices."""
    price = P0 * (1 - shock)
    alive = sorted(pop, key=lambda p: -p.liq)
    sold = fund = deficit = 0.0
    n_liq, path, step = 0, [(0, price, 0.0)], 0
    while alive and alive[0].liq >= price:
        trig = [p for p in alive if p.liq >= price]
        todo = trig if batch is None else trig[:batch]
        units = sum(p.units for p in todo)
        new = price - impact * units if forced_selling else price
        avg = 0.5 * (price + new)
        fund += sum(p.units * (avg - p.bankrupt) for p in todo)
        deficit += sum(p.units * max(0.0, p.bankrupt - avg) for p in todo)
        sold += units
        n_liq += len(todo)
        alive = alive[len(todo):]
        price = new
        step += 1
        path.append((step, price, sold))
    return Result(price, n_liq, sold, fund, deficit, path)


def drawdown_curve(pop: list[Long], shocks: list[float], **kw) -> list[tuple[float, float]]:
    return [(s, 1 - cascade(pop, s, **kw).price / P0) for s in shocks]


def critical_shock(pop: list[Long], level: float = 0.10, lo: float = 0.0, hi: float = 0.10, tol: float = 1e-5,
                   **kw) -> float:
    """Smallest initial shock after which the cascade takes the price down by at least `level` in all."""
    def deep(s: float) -> bool:
        return 1 - cascade(pop, s, **kw).price / P0 >= level
    if not deep(hi):
        return float("nan")
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        lo, hi = (lo, mid) if deep(mid) else (mid, hi)
    return hi


def local_multiplier(pop: list[Long], impact: float = 1.2e-5, width: float = 1.0) -> list[tuple[float, float]]:
    """kappa(P): price points of further fall caused by the liquidations in each price bin, per point of fall."""
    out = []
    top = int(P0)
    for lo in range(top - 1, 59, -1):
        units = sum(p.units for p in pop if lo < p.liq <= lo + width)
        out.append((lo + 0.5 * width, impact * units / width))
    return out
