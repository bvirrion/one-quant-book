"""Options quoting engine (build of Book 5, Chapter 26): theoretical values from a live surface, a width model, a
band delta hedger, the dividend play's arithmetic, and bucketed vega limits.

Rates are zero; surfaces are firm_volpnl.SkewSurface (sticky strike or sticky delta); prices per share.
"""
import math
import pathlib
import sys
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

FIRM = pathlib.Path(__file__).resolve().parents[1]
for comp in ("bs", "volpnl"):
    sys.path.insert(0, str(FIRM / comp))
from firm_bs import bs, greeks, ncdf, npdf  # noqa: E402
from firm_volpnl import Option, SkewSurface  # noqa: E402


# ---------------------------------------------------------------- theoretical value and width
def theo(o: Option, spot: float, t: float, surf: SkewSurface) -> tuple[float, float]:
    """Theoretical value and vega per volatility point of one option on the surface."""
    tau = o.expiry - t
    vol = surf.vol(o.strike, tau, spot)
    vega = greeks(spot, o.strike, tau, 0.0, 0.0, vol, o.right)["vega"]
    return bs(spot, o.strike, tau, 0.0, 0.0, vol, o.right), 0.01 * vega


def width_profit(w: float, s: float, lam_u: float, w_scale: float, lam_i: float) -> float:
    """Expected profit per unit time of quoting theo +- w when the theo's error X is N(0, s^2): uninformed orders
    arrive at lam_u exp(-w / w_scale) and earn w; informed orders arrive at lam_i and trade only when |X| > w,
    losing |X| - w."""
    z = w / s if s > 0 else math.inf
    tail = 2 * (s * npdf(z) - w * (1 - ncdf(z))) if s > 0 else 0.0
    return lam_u * math.exp(-w / w_scale) * w - lam_i * tail


def optimal_width(s: float, lam_u: float, w_scale: float, lam_i: float) -> float:
    """Half-width maximising width_profit, by golden-section search on [0, 6 s + 5 w_scale]."""
    lo, hi = 0.0, 6 * s + 5 * w_scale
    g = (math.sqrt(5) - 1) / 2
    for _ in range(200):
        a, b = hi - g * (hi - lo), lo + g * (hi - lo)
        if width_profit(a, s, lam_u, w_scale, lam_i) > width_profit(b, s, lam_u, w_scale, lam_i):
            hi = b
        else:
            lo = a
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------- delta hedging
def band_half_width(gamma: float, spot: float, cost: float, aversion: float, c: float = 1.0) -> float:
    """Hedging band half-width in shares, c (cost S Gamma^2 / aversion)^(1/3): the scaling that balances the
    rate of trading costs against the variance of the unhedged delta."""
    return c * (cost * spot * gamma * gamma / aversion) ** (1.0 / 3.0)


_ERF = np.vectorize(math.erf)


def _bs_vec(s: np.ndarray, k: float, tau: float, vol: float, right: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Price, delta and gamma of one option for an array of spots (flat volatility, zero rates)."""
    if tau <= 1e-12:
        pay = np.maximum(s - k, 0.0) if right == "C" else np.maximum(k - s, 0.0)
        return pay, np.zeros_like(s), np.zeros_like(s)
    sd = vol * math.sqrt(tau)
    d1 = np.log(s / k) / sd + 0.5 * sd
    n1, n2 = 0.5 * (1 + _ERF(d1 / math.sqrt(2))), 0.5 * (1 + _ERF((d1 - sd) / math.sqrt(2)))
    pdf = np.exp(-0.5 * d1 * d1) / math.sqrt(2 * math.pi)
    call, delta = s * n1 - k * n2, n1
    if right == "P":
        return call - s + k, delta - 1, pdf / (s * sd)
    return call, delta, pdf / (s * sd)


def hedge_paths(paths: np.ndarray, book: Sequence[Option], vol: float, dt: float, cost: float,
                band: float | None = None, every: int = 1) -> dict[str, np.ndarray]:
    """Delta-hedge a book along simulated paths (rows) at flat volatility, paying `cost` per unit of traded notional.
    With `band` = c the hedge trades back to the edge of the band c (cost S Gamma^2)^(1/3) when the delta leaves it;
    otherwise it re-hedges fully every `every` steps. Returns per-path P&L (after costs), costs and trade counts."""
    n, steps = paths.shape
    steps -= 1

    def book_at(s, t):
        v, d, g = np.zeros_like(s), np.zeros_like(s), np.zeros_like(s)
        for o in book:
            pv, pd, pg = _bs_vec(s, o.strike, o.expiry - t, vol, o.right)
            v, d, g = v + o.qty * pv, d + o.qty * pd, g + o.qty * pg
        return v, d, g
    hedge, cash, costs, trades = np.zeros(n), np.zeros(n), np.zeros(n), np.zeros(n)
    value0 = book_at(paths[:, 0], 0.0)[0]
    for i in range(steps):
        s = paths[:, i]
        _, delta, gamma = book_at(s, i * dt)
        if band is not None:
            h = band * (cost * s * gamma * gamma) ** (1.0 / 3.0)
            new = np.clip(hedge, -delta - h, -delta + h)
        else:
            new = -delta if i % every == 0 else hedge
        trade = new - hedge
        cash -= trade * s
        costs += cost * np.abs(trade) * s
        trades += np.abs(trade) > 1e-12
        hedge = new
    value_end = book_at(paths[:, -1], steps * dt)[0]
    pnl = value_end - value0 + cash + hedge * paths[:, -1] - costs
    return {"pnl": pnl, "costs": costs, "trades": trades}


# ---------------------------------------------------------------- the dividend play
def should_exercise(dividend: float, put_value: float) -> bool:
    """Exercise an in-the-money call on the eve of the ex-date when the dividend exceeds the value of the put with the
    same strike and expiry (the time value given up)."""
    return dividend > put_value


def dividend_play(public: float, fail: float, q: float, gain: float, trade_fee: float, exercise_fee: float) -> dict:
    """Two market makers trade q contracts twice with each other (each ends long q and short q) and exercise all their
    longs. Public holders own `public` contracts and a share `fail` of them does not exercise. Assignment falls pro
    rata on all short open interest (public + 2 q). Each short call left unassigned gains `gain` (the dividend less the
    time value); costs are four trade fees and two exercise fees per q. Returns the expected combined profit."""
    exercised = 2 * q + (1 - fail) * public
    shorts = public + 2 * q
    unassigned = 2 * q * (1 - exercised / shorts)
    cost = q * (4 * trade_fee + 2 * exercise_fee)
    return {"unassigned": unassigned, "gross": gain * unassigned, "cost": cost, "net": gain * unassigned - cost,
            "captured": unassigned / (fail * public) if fail > 0 else 0.0}


def best_play(public: float, fail: float, gain: float, trade_fee: float, exercise_fee: float) -> tuple[float, dict]:
    """The trade size q maximising the expected net profit: with a = 2 fail public gain and c the cost per q, the net is
    a q / (public + 2 q) - c q, maximal at q = (sqrt(a public / c) - public) / 2 (zero if negative)."""
    a = 2 * fail * public * gain
    c = 4 * trade_fee + 2 * exercise_fee
    q = max((math.sqrt(a * public / c) - public) / 2, 0.0) if c > 0 else math.inf
    return q, dividend_play(public, fail, q, gain, trade_fee, exercise_fee)


# ---------------------------------------------------------------- limits
@dataclass(frozen=True)
class Bucket:
    name: str
    lo: float        # expiry bounds in years, lo < tau <= hi
    hi: float
    limit: float     # absolute vega limit per volatility point


def vega_by_bucket(book: Sequence[Option], spot: float, t: float, surf: SkewSurface,
                   buckets: Sequence[Bucket]) -> dict[str, float]:
    out = dict.fromkeys((b.name for b in buckets), 0.0)
    for o in book:
        tau = o.expiry - t
        for b in buckets:
            if b.lo < tau <= b.hi:
                out[b.name] += o.qty * theo(o, spot, t, surf)[1]
    return out


def quote(o: Option, spot: float, t: float, surf: SkewSurface, half_width_vol: float, bucket_vega: float,
          limit: float, skew_at_limit: float = 1.0) -> tuple[float, float]:
    """Bid and ask around the theo, half-width in volatility points times vega; as the bucket's vega approaches its
    limit the quotes are shifted (in volatility points, up to skew_at_limit) to discourage trades that add to it,
    and the side that would breach the limit is withdrawn (NaN)."""
    value, vega = theo(o, spot, t, surf)
    use = bucket_vega / limit
    shift = skew_at_limit * max(min(use, 1.0), -1.0)
    bid = value - (half_width_vol + shift) * vega
    ask = value + (half_width_vol - shift) * vega
    if use >= 1.0:
        bid = math.nan
    if use <= -1.0:
        ask = math.nan
    return bid, ask
