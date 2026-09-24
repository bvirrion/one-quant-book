"""P&L explain, independent price verification and prudent valuation (build of One Quant Book 6, ch. 27).

- Risk-based attribution: the day's P&L as a Taylor expansion in the moves of the risk factors, from the
  Greeks of the start of day (delta, gamma, vega, volga, vanna, theta); the unexplained P&L is the rest.
- Revaluation-based attribution: move the factors one at a time from start to end of day and revalue in
  full; the steps add up to the P&L exactly, and their split depends on the order.
- Independent price verification: compare each trader mark with an independent consensus mid; a mark
  outside the tolerance is moved to the nearest boundary of the tolerance band.
- Prudent valuation: the market price uncertainty AVA of a position is the gap between its fair value and
  the value it would fetch with 90% confidence from the dispersion of consensus prices; category AVAs are
  summed after an aggregation factor of 50%.
"""
from collections.abc import Callable, Sequence
from statistics import NormalDist

ND = NormalDist()


def greeks(value: Callable[[dict], float], state: dict, bumps: dict) -> dict:
    """Central finite-difference Greeks of `value` at `state` for factors f (rate) and s (vol), and theta."""
    def v(**kw):
        return value({**state, **kw})

    f, s, hf, hs = state["f"], state["s"], bumps["f"], bumps["s"]
    v0 = v()
    out = {"delta": (v(f=f + hf) - v(f=f - hf)) / (2 * hf),
           "gamma": (v(f=f + hf) - 2 * v0 + v(f=f - hf)) / hf ** 2,
           "vega": (v(s=s + hs) - v(s=s - hs)) / (2 * hs),
           "volga": (v(s=s + hs) - 2 * v0 + v(s=s - hs)) / hs ** 2,
           "vanna": (v(f=f + hf, s=s + hs) - v(f=f + hf, s=s - hs) - v(f=f - hf, s=s + hs)
                     + v(f=f - hf, s=s - hs)) / (4 * hf * hs),
           "theta": v(t=state["t"] - bumps["t"]) - v0}          # per bump of time (one day)
    return out


def risk_based(g: dict, df: float, ds: float, days: float = 1.0, cross: bool = True) -> dict:
    out = {"delta": g["delta"] * df, "gamma": 0.5 * g["gamma"] * df * df, "vega": g["vega"] * ds,
           "volga": 0.5 * g["volga"] * ds * ds, "theta": g["theta"] * days,
           "vanna": g["vanna"] * df * ds if cross else 0.0}
    out["explained"] = sum(out.values())
    return out


def revaluation_based(value: Callable[[dict], float], start: dict, end: dict, order: Sequence[str]) -> dict:
    """Step-by-step revaluation: contributions of each factor moved in `order`."""
    state, prev, out = dict(start), value(start), {}
    for k in order:
        state[k] = end[k]
        now = value(state)
        out[k] = now - prev
        prev = now
    out["total"] = prev - value(start)
    return out


def ipv(marks: Sequence[float], consensus: Sequence[float], tolerance: Sequence[float]) -> list[tuple[float, float]]:
    """(verified mark, adjustment) per position: marks outside consensus +/- tolerance move to the boundary."""
    out = []
    for m, c, tol in zip(marks, consensus, tolerance, strict=True):
        v = min(max(m, c - tol), c + tol)
        out.append((v, v - m))
    return out


def mpu_ava(fair_value: float, consensus_mean: float, consensus_sd: float, quantity: float,
            confidence: float = 0.90) -> float:
    """Market price uncertainty AVA: fair value minus the value exited with `confidence`, on a normal
    dispersion of consensus prices (a long exits at the lower quantile, a short at the upper)."""
    z = ND.inv_cdf(confidence)
    prudent_price = consensus_mean - z * consensus_sd if quantity > 0 else consensus_mean + z * consensus_sd
    return max(0.0, fair_value - prudent_price * quantity)


def aggregate_ava(individual: Sequence[float], factor: float = 0.50) -> float:
    return factor * sum(individual)


def simplified_ava(fair_valued_abs_sum: float) -> float:
    """The simplified approach: 0.1% of the sum of absolute fair-valued assets and liabilities."""
    return 0.001 * fair_valued_abs_sum
