"""FRTB capital (build of One Quant Book 6, chapter 23), after BCBS d457 (January 2019).

Sensitivities-based method for the interest rate (GIRR) and FX risk classes: weighted sensitivities
WS = RW s, within-bucket K_b = sqrt(max(0, sum_kl rho_kl WS_k WS_l)), across buckets
sqrt(sum K_b^2 + sum_{b!=c} gamma_bc S_b S_c) (S_b clipped to [-K_b, K_b] if the sum is negative), under
the medium, high (x1.25, cap 1) and low (max(2 rho - 1, 0.75 rho)) correlation scenarios; GIRR tenor
risk weights and rho = max(exp(-3% |T_k - T_l| / min(T_k, T_l)), 40%), gamma 50% across currencies; FX
risk weight 15% (divided by sqrt 2 for specified pairs), gamma 60%; FX vega with risk weight 100%; FX
curvature with relative shocks equal to the delta risk weight. Internal models: expected shortfall
with liquidity-horizon scaling, IMCC = rho ES(all) + (1 - rho) sum ES(class), rho = 0.5, capital
max(IMCC_{t-1}; m_c avg) with m_c = 1.5; P&L attribution test (Spearman, Kolmogorov-Smirnov, zones);
risk-factor eligibility test; amber-zone surcharge.
"""
import math
from collections.abc import Sequence

import numpy as np

GIRR_TENORS = [0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 15.0, 20.0, 30.0]
GIRR_RW = dict(zip(GIRR_TENORS, [0.017, 0.017, 0.016, 0.013, 0.012, 0.011, 0.011, 0.011, 0.011, 0.011],
                   strict=True))
FX_RW, GIRR_GAMMA, FX_GAMMA, LH = 0.15, 0.50, 0.60, [10, 20, 40, 60, 120]


def girr_rho(t1: float, t2: float) -> float:
    return max(math.exp(-0.03 * abs(t1 - t2) / min(t1, t2)), 0.40)


def scenario(rho: float, which: str) -> float:
    if which == "high":
        return min(1.25 * rho, 1.0)
    if which == "low":
        return max(2 * rho - 1.0, 0.75 * rho)
    return rho


def within(ws: np.ndarray, corr: np.ndarray) -> float:
    return math.sqrt(max(0.0, float(ws @ corr @ ws)))


def across(K: Sequence[float], S: Sequence[float], gamma: float) -> float:
    K, S = np.asarray(K, float), np.asarray(S, float)
    n = len(K)

    def total(s):
        return float((K ** 2).sum() + sum(gamma * s[b] * s[c] for b in range(n) for c in range(n) if b != c))

    t = total(S)
    if t < 0:
        t = total(np.clip(S, -K, K))
    return math.sqrt(max(t, 0.0))


def girr_delta(sens: dict[str, dict[float, float]], which: str = "medium", specified: bool = True) -> float:
    """sens: currency -> {tenor: PV01 / 0.0001 (value change per unit rate)}."""
    Ks, Ss = [], []
    for ccy in sens:
        tenors = sorted(sens[ccy])
        ws = np.array([GIRR_RW[t] / (math.sqrt(2) if specified else 1.0) * sens[ccy][t] for t in tenors])
        corr = np.array([[1.0 if a == b else scenario(girr_rho(a, b), which) for b in tenors] for a in tenors])
        Ks.append(within(ws, corr))
        Ss.append(float(ws.sum()))
    return across(Ks, Ss, scenario(GIRR_GAMMA, which))


def fx_delta(sens: dict[str, float], which: str = "medium", specified: bool = True) -> float:
    """sens: currency -> value change for a 1% rise of the currency, divided by 0.01."""
    rw = FX_RW / (math.sqrt(2) if specified else 1.0)
    ws = [rw * s for s in sens.values()]
    return across([abs(w) for w in ws], ws, scenario(FX_GAMMA, which))


def fx_vega(sens: dict[str, float], which: str = "medium") -> float:
    """sens: currency pair -> vega x implied volatility (one maturity per bucket), risk weight 100%."""
    ws = list(sens.values())
    return across([abs(w) for w in ws], ws, scenario(FX_GAMMA, which))


def cvr(v0: float, v_up: float, v_dn: float, rw: float, delta: float) -> tuple[float, float]:
    """Net curvature charges CVR+ and CVR- for one risk factor (delta: sensitivity per unit relative move)."""
    return -(v_up - v0 - rw * delta), -(v_dn - v0 + rw * delta)


def fx_curvature(cvrs: dict[str, tuple[float, float]], which: str = "medium") -> float:
    Ks, Ss = [], []
    for up, dn in cvrs.values():
        kp, km = max(up, 0.0), max(dn, 0.0)
        if kp >= km:
            Ks.append(kp)
            Ss.append(up)
        else:
            Ks.append(km)
            Ss.append(dn)
    g = scenario(FX_GAMMA, which) ** 2
    n = len(Ks)
    t = sum(k * k for k in Ks) + sum(g * Ss[b] * Ss[c] * (0.0 if Ss[b] < 0 and Ss[c] < 0 else 1.0)
                                     for b in range(n) for c in range(n) if b != c)
    return math.sqrt(max(t, 0.0))


def sbm(parts: dict[str, callable]) -> dict:
    """parts: name -> function(which) -> charge. Sum per scenario; the requirement is the largest."""
    out = {w: sum(f(w) for f in parts.values()) for w in ("low", "medium", "high")}
    out["capital"] = max(out.values())
    return out


# ---- internal models ----------------------------------------------------------------------------------
def es(pnl: np.ndarray, alpha: float = 0.975) -> float:
    losses = np.sort(-np.asarray(pnl))[::-1]
    k = max(1, math.ceil((1 - alpha) * len(losses) - 1e-9))
    return float(losses[:k].mean())


def es_liquidity(es_by_horizon: Sequence[float], base: int = 10) -> float:
    """ES from ES_T(P, j), j = 1..5 (risk factors with liquidity horizon >= LH_j), MAR33.4."""
    tot = es_by_horizon[0] ** 2
    for j in range(1, len(es_by_horizon)):
        tot += (es_by_horizon[j] * math.sqrt((LH[j] - LH[j - 1]) / base)) ** 2
    return math.sqrt(tot)


def imcc(es_all: float, es_classes: Sequence[float], rho: float = 0.5) -> float:
    return rho * es_all + (1 - rho) * sum(es_classes)


def ima_capital(imcc_prev: float, imcc_avg: float, ses_prev: float = 0.0, ses_avg: float = 0.0,
                mc: float = 1.5) -> float:
    return max(imcc_prev + ses_prev, mc * imcc_avg + ses_avg)


def amber_surcharge(sa: float, ima: float, share_amber: float = 1.0) -> float:
    return 0.5 * share_amber * max(0.0, sa - ima)


def _ranks(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x, kind="mergesort")
    r = np.empty(len(x))
    r[order] = np.arange(len(x))
    return r


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.corrcoef(_ranks(np.asarray(a)), _ranks(np.asarray(b)))[0, 1])


def ks_stat(a: np.ndarray, b: np.ndarray) -> float:
    grid = np.sort(np.concatenate([a, b]))
    fa = np.searchsorted(np.sort(a), grid, side="right") / len(a)
    fb = np.searchsorted(np.sort(b), grid, side="right") / len(b)
    return float(np.max(np.abs(fa - fb)))


def pla_zone(sp: float, ks: float) -> str:
    if sp > 0.80 and ks < 0.09:
        return "green"
    if sp < 0.70 or ks > 0.12:
        return "red"
    return "amber"


def rfet(observation_days: Sequence[int], window: int = 365) -> bool:
    """Risk-factor eligibility test, criterion (1): at least 24 observations in the past year and no
    90-day period with fewer than four (days counted from the start of the year window)."""
    days = sorted(d for d in set(observation_days) if 0 <= d < window)
    if len(days) < 24:
        return False
    return all(sum(1 for d in days if s <= d < s + 90) >= 4 for s in range(0, window - 89))
