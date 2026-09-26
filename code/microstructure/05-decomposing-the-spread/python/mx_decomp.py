"""One Quant Book 10, chapter 5: decomposing the spread on the simulated market, where the truth is known.

    day()                           the 6.5-hour simulated session of chapter 3 (cached)
    truth(tape)                     effective half-spread and the efficient-price gap at trades (the true adverse part)
    by_horizon(tape, hs)            effective, realised and impact half-spreads by horizon, with standard errors and the
                                    impact net of the efficient price's own move (simulation only)
    var_by_lags(tape, specs)        the VAR's information share against the number of lags
    estimators(tape)                the information share by realised spreads, Glosten-Harris (100 and 500 shares),
                                    Huang-Stoll, MRR and the Hasbrouck VAR
    low_frequency(tape, bar_s)      Corwin-Schultz and Abdi-Ranaldo on bars against the effective spread
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("spreaddecomp", "tape"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_spreaddecomp import (  # noqa: E402
    abdi_ranaldo,
    corwin_schultz,
    decompose,
    glosten_harris,
    hasbrouck_var,
    huang_stoll,
    mid_at,
    mrr,
)
from firm_tape import TapeConfig, simulate  # noqa: E402


@functools.lru_cache(maxsize=1)
def day(seed: int = 7):
    return simulate(TapeConfig(seconds=23_400.0, u_shape=1.5, seed=seed, news_at=None))


def _mids(tape):
    return tape.top["t"], 0.5 * (tape.top["bid"] + tape.top["ask"])


def truth(tape) -> dict:
    """The simulator knows the efficient price P*: at each trade, eps (P*_t - m_t) is what the aggressor knew and the
    quotes did not show yet, the adverse selection the resting side pays (P* in firm.tape does not react to trades)."""
    tr = tape.trades
    t, mids = _mids(tape)
    m0 = mid_at(t, mids, tr["t"] - 1e-9)
    v0 = mid_at(tape.v_t, tape.v, tr["t"] - 1e-9)
    eps = tr["sign"].astype(float)
    w = tr["qty"] / tr["qty"].sum()
    eff = float(w @ (eps * (tr["price"] - m0)))
    adv = float(w @ (eps * (v0 - m0)))
    inf = tr["informed"]
    return {"effective": eff, "adverse": adv, "share": adv / eff,
            "informed_volume": float(tr["qty"][inf].sum() / tr["qty"].sum()),
            "gap_informed": float(np.average((eps * (v0 - m0))[inf], weights=tr["qty"][inf])),
            "gap_noise": float(np.average((eps * (v0 - m0))[~inf], weights=tr["qty"][~inf]))}


HORIZONS = (0.05, 1.0, 5.0, 15.0, 30.0, 60.0, 120.0, 300.0)


def by_horizon(tape, hs=HORIZONS, block_s: float = 600.0) -> dict:
    """Effective, realised and impact half-spreads (mid quotes, share-weighted) at each horizon, the standard error of
    the impact from 10-minute blocks, and the impact with the efficient price's own move removed, eps (m_{t+h} - m_t)
    - eps (P*_{t+h} - P*_t), which only a simulation can compute: it isolates the part of the move the trade caused."""
    tr = tape.trades
    t, mids = _mids(tape)
    eps = tr["sign"].astype(float)
    w = tr["qty"] / tr["qty"].sum()
    v0 = mid_at(tape.v_t, tape.v, tr["t"] - 1e-9)
    blk = (tr["t"] // block_s).astype(int)
    nb = int(blk.max()) + 1

    def se(x):
        means = [(w[blk == k] @ x[blk == k]) / w[blk == k].sum() for k in range(nb)]
        return float(np.std(means, ddof=1) / np.sqrt(nb))

    out = {}
    for h in hs:
        d = decompose(tr, t, mids, h)
        m0, mh = mid_at(t, mids, tr["t"] - 1e-9), mid_at(t, mids, tr["t"] + h)
        imp = eps * (mh - m0)
        clean = imp - eps * (mid_at(tape.v_t, tape.v, tr["t"] + h) - v0)
        out[h] = d | {"se": se(imp), "clean": float(w @ clean), "clean_se": se(clean)}
    return out


def var_by_lags(tape, specs=((1, 20), (5, 20), (10, 50), (20, 100), (50, 300), (100, 500))) -> dict:
    """The Hasbrouck VAR's permanent impact as a share of the effective half-spread, for (lags, steps) pairs."""
    tr = tape.trades
    t, mids = _mids(tape)
    r = np.diff(mid_at(t, mids, tr["t"] - 1e-9))
    x = tr["sign"][:-1].astype(float)
    eff = decompose(tr, t, mids, 60.0)["effective"]
    return {spec: hasbrouck_var(r, x, *spec)["permanent"] / eff for spec in specs}


def estimators(tape) -> dict:
    tr = tape.trades
    t, mids = _mids(tape)
    hs = huang_stoll(tr["price"], tr["sign"])
    g = glosten_harris(tr["price"], tr["sign"], tr["qty"] / 100.0)          # size in round lots of 100
    gh = {v: (g["z0"] + g["z1"] * v) / (g["z0"] + g["z1"] * v + g["c0"] + g["c1"] * v) for v in (1, 5)}
    m = mrr(tr["price"], tr["sign"])
    before = mid_at(t, mids, tr["t"] - 1e-9)
    r = np.diff(before)                                  # mid change from before trade i to before trade i+1
    var = hasbrouck_var(r, tr["sign"][:-1].astype(float))
    var_long = hasbrouck_var(r, tr["sign"][:-1].astype(float), lags=20, steps=100)
    eff = decompose(tr, t, mids, 60.0)["effective"]
    return {"realised_60s": decompose(tr, t, mids, 60.0)["impact_share"], "huang_stoll": hs["lam"],
            "hs_spread": hs["spread"], "gh_100": gh[1], "gh_500": gh[5], "mrr": m["info_share"], "mrr_rho": m["rho"],
            "var_permanent": var["permanent"], "var_share": var["permanent"] / eff,
            "var_long_share": var_long["permanent"] / eff}


def low_frequency(tape, bar_s: float = 60.0) -> dict:
    tr = tape.trades
    edges = np.arange(0.0, tape.cfg.seconds + bar_s, bar_s)
    k = np.searchsorted(edges, tr["t"], side="right") - 1
    hi, lo, cl = [], [], []
    for b in range(len(edges) - 1):
        p = tr["price"][k == b]
        if len(p):
            hi.append(p.max())
            lo.append(p.min())
            cl.append(p[-1])
    t, mids = _mids(tape)
    eff = decompose(tr, t, mids, 60.0)["effective"]
    mean_price = float(np.mean(tr["price"]))
    return {"bars": len(hi), "effective_rel": 2 * eff / mean_price, "cs": corwin_schultz(hi, lo),
            "ar": abdi_ranaldo(cl, hi, lo)}
