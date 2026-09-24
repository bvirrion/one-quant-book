"""Chapter 23 of Book 6: FRTB capital for chapter 21's book. Standardised approach (GIRR delta on the two-
and ten-year USD tenors, FX delta for EUR and JPY, FX vega and curvature of the EURUSD straddle) under
the three correlation scenarios; internal models (ten-day expected shortfall at 97.5% over the current
year and over the most severe twelve-month window since 2016, IMCC with rho = 0.5, m_c = 1.5); the P&L
attribution test of risk-theoretical against hypothetical P&L; the amber-zone surcharge."""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for p in ("code/firm/frtb", "code/rates-credit-risk/21-market-risk-measures/python"):
    sys.path.insert(0, str(ROOT / p))
import rc_var as rv  # noqa: E402
from firm_frtb import (  # noqa: E402
    FX_RW,
    amber_surcharge,
    cvr,
    es,
    fx_curvature,
    fx_delta,
    fx_vega,
    girr_delta,
    ima_capital,
    imcc,
    ks_stat,
    pla_zone,
    sbm,
    spearman,
)

SQ2 = math.sqrt(2.0)


def book():
    return rv.Book(rv.data()[1][-1])


def pnl(b, x) -> float:
    return float(b.pnl(np.asarray(x, dtype=float)[None, :])[0])


def sensitivities() -> dict:
    b = book()
    bp = 1e-4
    s2 = pnl(b, [bp, 0, 0, 0]) / bp
    s10 = pnl(b, [0, bp, 0, 0]) / bp
    s_eur = pnl(b, [0, 0, math.log(1.01), 0]) / 0.01
    s_jpy = pnl(b, [0, 0, 0, -math.log(1.01)]) / 0.01          # the yen up 1%: USDJPY / 1.01
    old = rv.VOL
    rv.VOL = old + 0.0001
    up = float(book().value(np.zeros((1, 4)))[0])
    rv.VOL = old
    vega = (up - float(b.value(np.zeros((1, 4)))[0])) / 0.0001
    # curvature of the straddle alone (the only option): full value against the linear term
    rw = FX_RW / SQ2
    e0 = b.eurusd

    def straddle_value(e):
        return -rv.STRADDLE * float(rv.straddle(np.array([e]), b.K, rv.T_OPT)[0])

    v0 = straddle_value(e0)
    s_opt = (straddle_value(e0 * 1.01) - v0) / 0.01
    cvr_up, cvr_dn = cvr(v0, straddle_value(e0 * (1 + rw)), straddle_value(e0 * (1 - rw)), rw, s_opt)
    return {"girr": {2.0: s2, 10.0: s10}, "fx": {"EUR": s_eur, "JPY": s_jpy}, "vega": vega * rv.VOL,
            "cvr": (cvr_up, cvr_dn), "s_opt": s_opt}


def standardised() -> dict:
    s = sensitivities()
    parts = {"girr": lambda w: girr_delta({"USD": s["girr"]}, w),
             "fx_delta": lambda w: fx_delta(s["fx"], w),
             "fx_vega": lambda w: fx_vega({"EURUSD": s["vega"]}, w),
             "fx_curv": lambda w: fx_curvature({"EURUSD": s["cvr"]}, w)}
    out = sbm(parts)
    out["parts"] = {k: f("medium") for k, f in parts.items()}
    out["parts_low"] = {k: f("low") for k, f in parts.items()}
    out["parts_high"] = {k: f("high") for k, f in parts.items()}
    return out


# ---- internal models ----------------------------------------------------------------------------------
def ten_day_moves(lv: np.ndarray) -> np.ndarray:
    """Overlapping ten-day factor moves."""
    return np.column_stack([lv[10:, 0] - lv[:-10, 0], lv[10:, 1] - lv[:-10, 1],
                            np.log(lv[10:, 2] / lv[:-10, 2]), np.log(lv[10:, 3] / lv[:-10, 3])])


def _masks():
    return {"all": np.ones(4), "rates": np.array([1, 1, 0, 0.0]), "fx": np.array([0, 0, 1, 1.0])}


def es_window(x: np.ndarray, mask) -> float:
    b = book()
    return es(b.pnl(x * mask))


def stressed_window() -> dict:
    d, lv = rv.data()
    x = ten_day_moves(lv)
    m = _masks()["all"]
    best, where = -1.0, 0
    for s in range(0, len(x) - 250, 5):
        v = es_window(x[s:s + 250], m)
        if v > best:
            best, where = v, s
    return {"start": d[where + 10], "end": d[where + 259], "x": x[where:where + 250], "es": best}


def internal_models() -> dict:
    d, lv = rv.data()
    cur = ten_day_moves(lv)[-250:]
    st = stressed_window()
    mk = _masks()
    es_cur = {k: es_window(cur, v) for k, v in mk.items()}
    es_st = {k: es_window(st["x"], v) for k, v in mk.items()}
    ratio = max(1.0, es_cur["all"] / es_cur["all"])          # reduced set = full set here
    i = imcc(es_st["all"] * ratio, [es_st["rates"], es_st["fx"]])
    return {"es_current": es_cur, "es_stressed": es_st, "stress": (st["start"], st["end"]), "imcc": i,
            "capital": ima_capital(i, i)}


# ---- P&L attribution --------------------------------------------------------------------------------
def pla(variant: str = "proxy_10y") -> dict:
    """HPL: full revaluation of the last 250 days' moves. RTPL: the risk model's P&L on the same days, from
    a model that proxies the ten-year yield by the two-year (proxy_10y), has no two-year factor (no_2y),
    has no yen factor (no_jpy), or revalues by the delta-gamma expansion (delta_gamma)."""
    d, lv = rv.data()
    x = rv.changes(lv)[-250:]
    b = book()
    hpl = b.pnl(x)
    y = x.copy()
    if variant == "delta_gamma":
        dl, g = b.greeks()
        rtpl = x @ dl + 0.5 * np.einsum("ni,ij,nj->n", x, g, x)
    else:
        if variant == "proxy_10y":
            y[:, 1] = x[:, 0]
        elif variant == "no_2y":
            y[:, 0] = 0.0
        elif variant == "no_jpy":
            y[:, 3] = 0.0
        rtpl = b.pnl(y)
    sp, ks = spearman(hpl, rtpl), ks_stat(hpl, rtpl)
    return {"spearman": sp, "ks": ks, "zone": pla_zone(sp, ks), "hpl": hpl, "rtpl": rtpl}


def desk_capital() -> dict:
    sa = standardised()["capital"]
    ima = internal_models()["capital"]
    sur = amber_surcharge(sa, ima)
    return {"sa": sa, "ima": ima, "surcharge": sur, "amber_total": ima + sur}
