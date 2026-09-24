"""Chapter 21 of Book 6: market-risk measures on public data. A small USD book: long USD 200m of a ten-year
Treasury par bond, short USD 300m of a two-year, long EUR 100m, short JPY 5bn, and short a three-month
at-the-money EURUSD straddle on EUR 400m (8% volatility held). Risk factors: daily changes of the two- and
ten-year par yields (US Treasury) and log returns of EURUSD and USDJPY (ECB reference rates). One-day 99%
VaR and 97.5% ES by historical simulation, EWMA parametric, Monte Carlo and filtered historical simulation;
delta-gamma against full revaluation; a four-year backtest with Kupiec, Christoffersen and the traffic light;
Euler contributions."""
import csv
import math
import pathlib
import sys
from statistics import NormalDist

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/varmodel"))
from firm_varmodel import (  # noqa: E402
    christoffersen,
    delta_gamma,
    euler_var,
    ewma_cov,
    fhs_scenarios,
    hs_var_es,
    kupiec,
    mc_var_es,
    parametric_var_es,
    traffic_light,
)

ND = NormalDist()
WINDOW, LAM = 500, 0.94
R_USD, R_EUR, VOL, T_OPT, STRADDLE = 0.04, 0.02, 0.08, 0.25, 400e6


_DATA: list = []
_MEAS: list = []


def data():
    if not _DATA:
        _DATA.append(_load())
    return _DATA[0]


def _load():
    with open(ROOT / "data/rates-credit-risk/treasury_par_yields.csv") as fh:
        ty = {r["date"]: (float(r["y2"]) / 100, float(r["y10"]) / 100)
              for r in csv.DictReader(fh) if r["y2"] and r["y10"]}
    with open(ROOT / "data/rates-credit-risk/ecb_fx_2016_2026.csv") as fh:
        fx = {r["date"]: (float(r["usd_per_eur"]), float(r["jpy_per_eur"]) / float(r["usd_per_eur"]))
              for r in csv.DictReader(fh)}
    dates = sorted(set(ty) & set(fx))
    lv = np.array([[*ty[d], *fx[d]] for d in dates])        # y2, y10, EURUSD, USDJPY
    return dates, lv


def changes(lv: np.ndarray) -> np.ndarray:
    return np.column_stack([np.diff(lv[:, 0]), np.diff(lv[:, 1]), np.diff(np.log(lv[:, 2])), np.diff(np.log(lv[:, 3]))])


def par_bond(y: np.ndarray, coupon: float, years: int) -> np.ndarray:
    """Price per unit of a semi-annual bond at yield y (vectorised)."""
    n = 2 * years
    d = 1 + np.asarray(y) / 2
    return coupon / 2 * (1 - d ** -n) / (np.asarray(y) / 2) + d ** -n


def straddle(S: np.ndarray, K: float, t: float) -> np.ndarray:
    """Garman-Kohlhagen call plus put on one euro, USD value."""
    S = np.asarray(S, dtype=float)
    f = S * math.exp((R_USD - R_EUR) * t)
    sd = VOL * math.sqrt(t)
    d1 = (np.log(f / K) + 0.5 * sd * sd) / sd
    cdf = np.vectorize(ND.cdf)
    call = math.exp(-R_USD * t) * (f * cdf(d1) - K * cdf(d1 - sd))
    put = math.exp(-R_USD * t) * (K * cdf(-(d1 - sd)) - f * cdf(-d1))
    return call + put


class Book:
    def __init__(self, level: np.ndarray):
        self.y2, self.y10, self.eurusd, self.usdjpy = level
        self.K = self.eurusd * math.exp((R_USD - R_EUR) * T_OPT)      # ATM forward strike

    def value(self, x: np.ndarray) -> np.ndarray:
        """Book value (USD) after factor moves x (n x 4), time held."""
        x = np.atleast_2d(x)
        y2, y10 = self.y2 + x[:, 0], self.y10 + x[:, 1]
        e, j = self.eurusd * np.exp(x[:, 2]), self.usdjpy * np.exp(x[:, 3])
        return (200e6 * par_bond(y10, self.y10, 10) - 300e6 * par_bond(y2, self.y2, 2) + 100e6 * e - 5e9 / j
                - STRADDLE * straddle(e, self.K, T_OPT))

    def pnl(self, x: np.ndarray) -> np.ndarray:
        return self.value(x) - self.value(np.zeros((1, 4)))[0]

    def greeks(self, h=(1e-5, 1e-5, 1e-4, 1e-4)) -> tuple[np.ndarray, np.ndarray]:
        h = np.array(h)
        d, g = np.zeros(4), np.zeros((4, 4))
        e = np.eye(4) * h
        for i in range(4):
            d[i] = (self.pnl(e[i])[0] - self.pnl(-e[i])[0]) / (2 * h[i])
            for j in range(4):
                g[i, j] = (self.pnl(e[i] + e[j])[0] - self.pnl(e[i] - e[j])[0] - self.pnl(-e[i] + e[j])[0]
                           + self.pnl(-e[i] - e[j])[0]) / (4 * h[i] * h[j])
        return d, g


def today():
    dates, lv = data()
    x = changes(lv)[-WINDOW:]
    return dates, lv, x, Book(lv[-1])


def measures() -> dict:
    if not _MEAS:
        _MEAS.append(_measures())
    return _MEAS[0]


def _measures() -> dict:
    dates, lv, x, book = today()
    pnl_hs = book.pnl(x)
    cov_ew, cov_eq = ewma_cov(x, LAM), np.cov(x.T, bias=True)
    delta, gamma = book.greeks()
    out = {"date": dates[-1], "levels": lv[-1], "delta": delta, "gamma": gamma}
    out["hs"] = hs_var_es(pnl_hs, 0.99), hs_var_es(pnl_hs, 0.975)
    out["param_ewma"] = parametric_var_es(delta, cov_ew, 0.99), parametric_var_es(delta, cov_ew, 0.975)
    out["param_eq"] = parametric_var_es(delta, cov_eq, 0.99), parametric_var_es(delta, cov_eq, 0.975)
    out["mc"] = mc_var_es(book.pnl, cov_ew, 0.99), mc_var_es(book.pnl, cov_ew, 0.975)
    fx = fhs_scenarios(changes(lv)[-(WINDOW + 250):], LAM)[-WINDOW:]
    p_fhs = book.pnl(fx)
    out["fhs"] = hs_var_es(p_fhs, 0.99), hs_var_es(p_fhs, 0.975)
    out["dg"] = hs_var_es(delta_gamma(delta, gamma, x), 0.99), hs_var_es(delta_gamma(delta, gamma, x), 0.975)
    out["delta_only"] = hs_var_es(x @ delta, 0.99)
    out["euler"] = euler_var(delta, cov_ew, 0.99)
    out["pnl_hs"] = pnl_hs
    out["pnl_dg"] = delta_gamma(delta, gamma, x)
    return out


_BT: dict = {}


def backtest(days: int = 1000) -> dict:
    if days not in _BT:
        _BT[days] = _backtest(days)
    return _BT[days]


def _backtest(days: int) -> dict:
    """Rolling one-day 99% VaR on the fixed book, repriced at each day's levels, against the next day's P&L."""
    dates, lv = data()
    x = changes(lv)
    n = len(x)
    rows = []
    for t in range(n - days, n):
        book = Book(lv[t])
        win = x[t - WINDOW:t]
        realised = float(book.pnl(x[t:t + 1])[0])
        v_hs = hs_var_es(book.pnl(win), 0.99)[0]
        d, _ = book.greeks()
        v_ew = parametric_var_es(d, ewma_cov(win, LAM), 0.99)[0]
        v_fhs = hs_var_es(book.pnl(fhs_scenarios(x[t - WINDOW - 250:t], LAM)[-WINDOW:]), 0.99)[0]
        rows.append((dates[t + 1], realised, v_hs, v_ew, v_fhs))
    out = {"rows": rows}
    for k, name in ((2, "hs"), (3, "ewma"), (4, "fhs")):
        hits = np.array([r[1] < -r[k] for r in rows], dtype=int)
        last = hits[-250:]
        out[name] = {"exceptions": int(hits.sum()), "kupiec": kupiec(len(hits), int(hits.sum()), 0.01),
                     "christoffersen": christoffersen(hits), "last250": int(last.sum()),
                     "zone": traffic_light(int(last.sum())), "hits": hits}
    return out


def capital(zone_add: float) -> dict:
    """Internal-models style charge: (3 + backtesting add-on) x ten-day 99% VaR (square-root-of-time)."""
    v = measures()["param_ewma"][0][0]
    ten = v * math.sqrt(10)
    return {"var1": v, "var10": ten, "base": 3 * ten, "with_addon": (3 + zone_add) * ten}


def method_table():
    o = measures()
    return [(n, o[k][0][0] / 1e6, o[k][1][1] / 1e6) for n, k in (("HS", "hs"), ("EWMA", "param_ewma"),
            ("equal-wt", "param_eq"), ("MC", "mc"), ("FHS", "fhs"), ("HS delta-gamma", "dg"))]


def histogram(bins: int = 40):
    p = measures()["pnl_hs"] / 1e6
    counts, edges = np.histogram(p, bins=bins)
    return [(0.5 * (edges[i] + edges[i + 1]), int(counts[i])) for i in range(bins)]
