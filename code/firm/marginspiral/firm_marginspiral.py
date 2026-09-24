"""Multi-asset margin-spiral simulator (build of Book 3, Chapter 28).

Leveraged holders own several assets on margin. Margin rates rise with an exponentially weighted
estimate of each asset's volatility (the margin spiral); losses reduce equity (the loss spiral). A
holder whose equity falls below its requirement sells the same fraction of every position to restore
it, and sales move prices through a linear permanent impact, which cuts every holder's equity. Switches
turn each mechanism off for ablation. Time is in days, split into `substeps` for stability checks.
"""
import math
import random
from dataclasses import dataclass, field


@dataclass
class Params:
    vols: tuple = (0.006, 0.004, 0.010)          # daily volatilities of the three assets in calm
    corr: float = 0.2                            # correlation of their exogenous returns
    base_margin: tuple = (0.10, 0.05, 0.15)      # margin rates in calm
    impact: tuple = (2.0e-12, 1.0e-12, 4.0e-12)  # log price move per dollar sold
    holders: int = 40
    leverage: float = 8.0                        # positions over equity at the start
    days: int = 40
    shock_day: int = 10
    shock: tuple = (-0.10, 0.0, 0.0)             # exogenous move on the shock day
    ewma: float = 0.94
    substeps: int = 1
    margin_spiral: bool = True
    loss_spiral: bool = True
    cross_holding: bool = True
    forced_selling: bool = True
    seed: int = 28


@dataclass
class Result:
    prices: list = field(default_factory=list)          # per day, per asset
    returns: list = field(default_factory=list)
    forced_sales: float = 0.0                            # dollars sold by force over the run
    initial_shortfall: float = 0.0                       # margin shortfall right after the shock, dollars
    defaults: int = 0


def _correlated_normals(rng: random.Random, corr: float, n: int) -> list[float]:
    common = rng.gauss(0, 1)
    return [math.sqrt(corr) * common + math.sqrt(1 - corr) * rng.gauss(0, 1) for _ in range(n)]


def simulate(p: Params) -> Result:
    rng = random.Random(p.seed)
    k = len(p.vols)
    prices = [100.0] * k
    var = [v * v for v in p.vols]
    # every holder has 1 billion of equity; with cross-holding it holds all assets equally, else one each
    equity = [1e9] * p.holders
    pos = []
    for h in range(p.holders):
        w = [1 / k] * k if p.cross_holding else [1.0 if j == h % k else 0.0 for j in range(k)]
        pos.append([p.leverage * 1e9 * w[j] / prices[j] for j in range(k)])
    res = Result()
    dt = 1 / p.substeps
    for day in range(p.days):
        start = prices[:]
        for sub in range(p.substeps):
            z = _correlated_normals(rng, p.corr, k)
            r = [p.vols[j] * math.sqrt(dt) * z[j] for j in range(k)]
            if day == p.shock_day and sub == 0:
                r = [r[j] + p.shock[j] for j in range(k)]
            _move(prices, pos, equity, r, p)
            for j in range(k):
                var[j] = p.ewma ** dt * var[j] + (1 - p.ewma ** dt) * (r[j] * r[j] / dt)
            rates = [p.base_margin[j] * (math.sqrt(var[j]) / p.vols[j] if p.margin_spiral else 1.0) for j in range(k)]
            shortfall_now = sum(max(0.0, _req(pos[h], prices, rates) - equity[h]) for h in range(p.holders))
            if day == p.shock_day and sub == 0:
                res.initial_shortfall = shortfall_now
            if p.forced_selling:
                for _ in range(100):                     # deleverage to a fixed point within the step
                    sold = _deleverage(prices, pos, equity, rates, p, res)
                    res.forced_sales += sum(sold)
                    if sum(sold) < 1e3:
                        break
        res.prices.append(prices[:])
        res.returns.append([prices[j] / start[j] - 1 for j in range(k)])
    return res


def _req(q: list[float], prices: list[float], rates: list[float]) -> float:
    return sum(rates[j] * abs(q[j]) * prices[j] for j in range(len(q)))


def _move(prices, pos, equity, r, p: Params) -> None:
    """Apply log returns r to prices and, with the loss spiral on, the P&L to every holder's equity."""
    for j in range(len(prices)):
        old = prices[j]
        prices[j] = old * math.exp(r[j])
        if p.loss_spiral:
            for h in range(len(pos)):
                equity[h] += pos[h][j] * (prices[j] - old)


def _deleverage(prices, pos, equity, rates, p: Params, res: Result) -> list[float]:
    """Holders below their requirement sell the fraction 1 - equity / requirement of every position (all of
    it if equity is gone); the dollars sold per asset then move prices by the linear impact."""
    k = len(prices)
    sold = [0.0] * k
    for h in range(len(pos)):
        req = _req(pos[h], prices, rates)
        if req <= 0 or equity[h] >= req:
            continue
        x = 1.0 if equity[h] <= 0 else 1 - equity[h] / req
        if equity[h] <= 0 and any(pos[h]):
            res.defaults += 1
        for j in range(k):
            dq = x * pos[h][j]
            sold[j] += dq * prices[j]
            pos[h][j] -= dq
    impact = [-p.impact[j] * sold[j] for j in range(k)]
    if any(impact):
        _move(prices, pos, equity, impact, p)
    return sold


def forced_sale_multiplier(res: Result) -> float:
    """Dollars sold by force per dollar of margin shortfall created by the shock."""
    return res.forced_sales / res.initial_shortfall if res.initial_shortfall else 0.0


def correlation(res: Result, a: int, b: int, days: range) -> float:
    xs = [res.returns[d][a] for d in days]
    ys = [res.returns[d][b] for d in days]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    return sxy / math.sqrt(sxx * syy)
