"""The structured-products business (Book 5, Chapter 19): a capital-protected note's participation against the
issuer's funding spread, a capped note, a reverse convertible, and options on a volatility-target index and on
a decrement index. Rates 3%, dividend yield 1.5%, chapter 9's surface for the options."""
import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for comp in ("bs", "svi", "heston", "termsheet"):
    sys.path.insert(0, str(ROOT / f"code/firm/{comp}"))
sys.path.insert(0, str(ROOT / "code/derivatives/10-stochastic-volatility/python"))
from dv_heston import calibration  # noqa: E402
from firm_bs import bs, implied_vol  # noqa: E402
from firm_heston import simulate_paths  # noqa: E402
from firm_svi import ssvi  # noqa: E402
from firm_termsheet import (  # noqa: E402
    decrement_index,
    max_participation,
    protected_note,
    reverse_convertible_coupon,
    spread_for_participation,
    value,
    vol_target_index,
    zero_coupon,
)

R, Q, T, MARGIN = 0.03, 0.015, 2.0, 1.5


def smile(t: float):
    """Chapter 9's surface in forward moneyness, read at a strike relative to spot."""
    theta = (0.20 - 0.06 * math.exp(-t / 0.5)) ** 2 * t
    fwd = math.exp((R - Q) * t)
    return lambda k: math.sqrt(float(ssvi(math.log(k / fwd), theta, -0.6, 1.0, 0.45)) / t)


def participation_curve(spreads=None) -> list[tuple[float, float]]:
    spreads = np.arange(0.0, 0.0301, 0.0025) if spreads is None else spreads
    vol = smile(T)
    return [(s, max_participation(T, R, s, Q, vol, MARGIN)) for s in spreads]


def named_result() -> dict:
    vol = smile(T)
    s = spread_for_participation(0.70, T, R, Q, vol, MARGIN)
    unit = value(protected_note(T, 1.0, 0.0), R, 0.0, Q, vol)
    return {"spread": s, "call": unit, "zc_at_spread": zero_coupon(T, R, s), "zc_riskfree": zero_coupon(T, R, 0.0),
            "p_at_50bp": max_participation(T, R, 0.005, Q, vol, MARGIN),
            "p_at_0": max_participation(T, R, 0.0, Q, vol, MARGIN)}


def capped_note(spread: float = 0.01) -> dict:
    """Full participation up to a cap: find the cap that the budget allows."""
    vol = smile(T)
    lo, hi = 1.01, 3.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if max_participation(T, R, spread, Q, vol, MARGIN, cap=mid) > 1.0:
            lo = mid
        else:
            hi = mid
    return {"cap": 0.5 * (lo + hi), "uncapped": max_participation(T, R, spread, Q, vol, MARGIN)}


def reverse_convertible(spread: float = 0.01, strike: float = 0.9, t: float = 1.0) -> dict:
    vol = smile(t)
    c = reverse_convertible_coupon(t, R, spread, Q, vol, strike, MARGIN)
    put = 100 / strike * bs(1.0, strike, t, R, Q, vol(strike), "P")
    return {"coupon": c, "put": put, "funding": 100 - zero_coupon(t, R, spread)}


# ---------------------------------------------------------------- strategy indices under Heston
@functools.cache
def heston_daily(n: int = 40_000, seed: int = 19) -> np.ndarray:
    """One year of daily closes under chapter 10's Heston model (zero rates: the index's excess return)."""
    days = np.arange(1, 253) / 252
    return simulate_paths(calibration()[0], 1.0, days, 252, n, seed)


def vol_target_options(strikes=(0.9, 1.0, 1.1)) -> dict:
    """Calls on the raw index and on a 10% volatility-target index built on it (zero rates), and the implied
    volatilities of each."""
    p = heston_daily()
    rets = p[:, 1:] / p[:, :-1] - 1
    vt = vol_target_index(rets, 0.10)
    out = {"raw": [], "vt": [], "raw_iv": [], "vt_iv": []}
    for k in strikes:
        for name, x in (("raw", p[:, -1]), ("vt", vt[:, -1])):
            c = float(np.maximum(x - k, 0).mean())
            f = float(x.mean())
            out[name].append(c)
            out[name + "_iv"].append(implied_vol(c, f, k, 1.0, 1.0, "C"))
    realised = {"raw": float(np.mean(np.std(np.log(p[:, 1:] / p[:, :-1]), axis=1) * math.sqrt(252))),
                "vt": float(np.mean(np.std(np.log(vt[:, 1:] / vt[:, :-1]), axis=1) * math.sqrt(252)))}
    dispersion = {"raw": float(np.std(np.std(np.log(p[:, 1:] / p[:, :-1]), axis=1) * math.sqrt(252))),
                  "vt": float(np.std(np.std(np.log(vt[:, 1:] / vt[:, :-1]), axis=1) * math.sqrt(252)))}
    out["realised"], out["realised_sd"] = realised, dispersion
    return out


def vt_sample_path(i: int = 7) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    p = heston_daily()
    rets = p[:, 1:] / p[:, :-1] - 1
    vt = vol_target_index(rets, 0.10)
    from firm_termsheet import ewma_vol
    ex = np.minimum(0.10 / ewma_vol(rets[i:i + 1]), 1.5)[0]
    return p[i], vt[i], ex


def decrement_example(dividend: float = 0.03, decrement: float = 0.05, t: float = 5.0) -> dict:
    """Forward of a 5% decrement index built on a total-return index against the price index paying 3% dividends,
    and five-year at-the-money puts on each (flat 20% volatility, 3% rate)."""
    fwd_price = math.exp((R - dividend) * t)
    fwd_dec = math.exp((R - decrement) * t)
    put_price = bs(1.0, 1.0, t, R, dividend, 0.2, "P")
    put_dec = bs(1.0, 1.0, t, R, decrement, 0.2, "P")
    days = np.arange(0, round(252 * t) + 1)
    tr = np.exp(R * days / 252)[None, :]
    level = decrement_index(tr, decrement)[0]
    return {"fwd_price": fwd_price, "fwd_dec": fwd_dec, "put_price": put_price, "put_dec": put_dec,
            "days": days, "dec_path": level / 100.0}
