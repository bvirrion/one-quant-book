"""Book 3, Chapter 20: impermanent loss, loss-versus-rebalancing measured by simulation against its closed
form sigma^2 / 8, concentrated ranges, and the turnover at which fees pay for LVR."""
import math
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/amm"))
from firm_amm import ss_get_y  # noqa: E402


def impermanent_loss(r: float) -> float:
    """Full-range constant product: pool value over holding the initial tokens, minus one, after the price
    moves by a factor r."""
    return 2 * math.sqrt(r) / (1 + r) - 1


def range_value(p: float, pa: float, pb: float, liq: float = 1.0) -> float:
    """Value in token1 of a concentrated position of liquidity L over [pa, pb] at price p."""
    s, sa, sb = math.sqrt(min(max(p, pa), pb)), math.sqrt(pa), math.sqrt(pb)
    x = liq * (1 / s - 1 / sb)
    y = liq * (s - sa)
    return x * p + y


def impermanent_loss_range(r: float, width: float) -> float:
    """Concentrated position over [p0/(1+w), p0 (1+w)] entered at p0 = 1, against holding its tokens."""
    pa, pb = 1 / (1 + width), 1 + width
    s, sa, sb = 1.0, math.sqrt(pa), math.sqrt(pb)
    x0, y0 = 1 / s - 1 / sb, s - sa
    return range_value(r, pa, pb) / (x0 * r + y0) - 1


def lvr_path(sigma: float, days: int, steps_per_day: int, seed: int) -> tuple[list[float], float]:
    """Arbitrageurs move a fee-free constant-product pool to the market price at every step of a driftless
    lognormal path. Returns the cumulative LVR (rebalancing portfolio minus pool, as a fraction of the
    initial pool value) at the end of each day, and the closed form sigma^2/8 per year integrated."""
    rng = random.Random(seed)
    dt = 1 / (365 * steps_per_day)
    p, liq = 1.0, 1.0
    pool0 = 2 * liq * math.sqrt(p)
    rebal, out, theory = pool0, [], 0.0
    for _ in range(days):
        for _ in range(steps_per_day):
            x, v_before, p_before = liq / math.sqrt(p), 2 * liq * math.sqrt(p), p
            p *= math.exp(-0.5 * sigma * sigma * dt + sigma * math.sqrt(dt) * rng.gauss(0, 1))
            rebal += x * (p - p_before)                     # hold the pool's risky position, rebalance
            theory += sigma * sigma / 8 * dt * v_before
        out.append((rebal - 2 * liq * math.sqrt(p)) / pool0)
    return out, theory / pool0


def lvr_mean(sigma: float = 0.6, days: int = 30, steps_per_day: int = 96, paths: int = 200) -> tuple[list, float]:
    """Average cumulative LVR over paths, with the closed form for comparison (fraction of pool value)."""
    acc, th = [0.0] * days, 0.0
    for k in range(paths):
        path, t = lvr_path(sigma, days, steps_per_day, 20 + k)
        acc = [a + b / paths for a, b in zip(acc, path, strict=True)]
        th += t / paths
    return acc, th


def breakeven_turnover(sigma_annual: float, fee: float) -> float:
    """Daily volume over pool value at which fee income equals LVR: sigma_daily^2 / (8 fee)."""
    return sigma_annual**2 / 365 / (8 * fee)


def stableswap_curve(amp: int = 85, total: float = 10.0) -> list[tuple[float, float]]:
    """Points of the stableswap invariant for two coins with D = total, from Curve's integer solver."""
    e = 10**12
    half = int(total / 2 * e)
    xp = [half, half]
    pts = []
    for k in range(1, 41):
        x = k * 0.5
        y = ss_get_y(0, 1, int(x * e), xp, amp) / e
        pts.append((x, y))
    return pts
