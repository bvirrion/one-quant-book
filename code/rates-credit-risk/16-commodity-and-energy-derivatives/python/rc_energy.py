"""Chapter 16 of Book 6: commodity and energy derivatives. An illustrative Henry Hub-like forward curve
(April to March, $/MMBtu) and a two-factor forward-curve model calibrated to synthetic option volatilities;
calendar-spread options by Kirk's approximation and Monte Carlo; a storage facility valued by intrinsic,
rolling intrinsic and least-squares Monte Carlo; a winter swing contract; and the February 2021 cold snap
in EIA's daily Henry Hub prices, captured by a fast and a slow storage facility."""
import csv
import datetime as dt
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/energymodel"))
from firm_energymodel import (  # noqa: E402
    Facility,
    TwoFactor,
    calibrate,
    intrinsic,
    kirk,
    lsm,
    margrabe,
    rolling_intrinsic,
    spot_paths,
    spread_mc,
    swing_facility,
)

MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
F0 = [2.60, 2.62, 2.68, 2.74, 2.78, 2.80, 2.90, 3.20, 3.45, 3.50, 3.30, 3.00]    # illustrative, $/MMBtu
T = [k / 12 + 1 / 24 for k in range(12)]                                          # mid-month delivery
R_FREE = 0.04
DFS = [math.exp(-R_FREE * t) for t in T]
TRUE = TwoFactor(1.5, 0.60, 0.20, 0.30)          # generates the synthetic option quotes
RHO = 0.30
UNIT = 100_000                                    # MMBtu per volume unit
FACILITY = Facility(capacity=10, max_inject=2, max_withdraw=4, cost_in=0.02, cost_out=0.02)
PATHS = 4000


def vol_quotes() -> list[tuple[float, float, float]]:
    """Synthetic implied volatilities of options expiring half a month before each delivery (rounded to 0.1%)."""
    return [(t - 1 / 24, t, round(TRUE.implied_vol(t - 1 / 24, t), 3)) for t in T[1:]]


def model() -> TwoFactor:
    return calibrate(vol_quotes(), RHO)


def inst_vol(m: TwoFactor, tau: float) -> float:
    return math.sqrt(m.sigma_s ** 2 * math.exp(-2 * m.kappa * tau) + m.sigma_l ** 2
                     + 2 * m.rho * m.sigma_s * m.sigma_l * math.exp(-m.kappa * tau))


def calendar_spread(K: float = 0.5, m: TwoFactor | None = None) -> dict:
    """Call on the January forward minus the July forward, strike K, expiring at July delivery."""
    m = m or model()
    te, T1, T2 = T[3], T[9], T[3]
    s1, s2 = m.implied_vol(te, T1), m.implied_vol(te, T2)
    rho = m.cov(te, T1, T2) / math.sqrt(m.var(te, T1) * m.var(te, T2))
    df = math.exp(-R_FREE * te)
    mc, se = spread_mc(F0[9], F0[3], K, te, s1, s2, rho, df)
    return {"s1": s1, "s2": s2, "rho": rho, "kirk": kirk(F0[9], F0[3], K, te, s1, s2, rho, df),
            "margrabe": margrabe(F0[9], F0[3], te, s1, s2, rho, df), "mc": mc, "se": se,
            "intrinsic": df * max(F0[9] - F0[3] - K, 0.0)}


def storage() -> dict:
    m = model()
    iv, plan = intrinsic(FACILITY, F0, DFS)
    S = spot_paths(m, F0, T, PATHS)
    ri = rolling_intrinsic(FACILITY, m, F0, T, DFS, PATHS)
    ls = lsm(FACILITY, S, DFS)
    return {"intrinsic": iv, "plan": plan, "rolling": ri, "lsm": ls, "extrinsic": ls - iv}


def swing() -> dict:
    """Winter swing: November to March, up to 2 units a month, 6 units in all, strike $3.10."""
    m = model()
    fac = swing_facility(6, 2, 3.10)
    S = spot_paths(m, F0, T, PATHS)
    iv, plan = intrinsic(fac, F0[7:], DFS[7:])
    strip = sum(2 * black_call(F0[k], 3.10, T[k], m.implied_vol(T[k], T[k]), DFS[k]) for k in range(7, 12))
    return {"intrinsic": iv, "plan": plan, "lsm": lsm(fac, S[:, 7:], DFS[7:]), "strip": strip}


def black_call(F: float, K: float, t: float, vol: float, df: float) -> float:
    from statistics import NormalDist
    n = NormalDist()
    d1 = (math.log(F / K) + 0.5 * vol * vol * t) / (vol * math.sqrt(t))
    return df * (F * n.cdf(d1) - K * n.cdf(d1 - vol * math.sqrt(t)))


# ---- February 2021 ----------------------------------------------------------------------------------
def henry_hub() -> list[tuple[dt.date, float]]:
    with open(ROOT / "data/rates-credit-risk/henry_hub_daily_2020_2021.csv") as fh:
        return [(dt.date.fromisoformat(r["date"]), float(r["price"])) for r in csv.DictReader(fh)]


def storm(start=dt.date(2021, 2, 8), end=dt.date(2021, 2, 19), fast: int = 100_000, slow: int = 10_000,
          held: int = 500_000, cost: float = 0.02) -> dict:
    """Sell `rate` MMBtu a day on the best storm days (up to `held`), buy the same volume back at the
    March 2021 average: the value a fast and a slow facility could capture."""
    hh = henry_hub()
    days = sorted([(p, d) for d, p in hh if start <= d <= end], reverse=True)
    march = [p for d, p in hh if d.year == 2021 and d.month == 3]
    rebuy = sum(march) / len(march)
    out = {"rebuy": rebuy, "peak": max(days)[0], "peak_day": max(days)[1].isoformat(),
           "feb1": [p for d, p in hh if d == dt.date(2021, 2, 1)][0]}
    for label, rate in (("fast", fast), ("slow", slow)):
        vol, cash, used = 0, 0.0, []
        for p, d in days:
            q = min(rate, held - vol)
            if q <= 0 or p - rebuy - 2 * cost <= 0:
                continue
            vol += q
            cash += q * (p - rebuy - 2 * cost)
            used.append(d.isoformat())
        out[label] = {"volume": vol, "value": cash, "days": len(used)}
    return out


def curve_table():
    iv, plan = intrinsic(FACILITY, F0, DFS)
    inv, rows = 0, []
    for k, (f, a) in enumerate(zip(F0, plan, strict=True)):
        inv += a
        rows.append((k + 1, f, a, inv))
    return rows


def vol_table():
    m = model()
    q = {round(te + 1 / 24, 6): v for te, _, v in vol_quotes()}
    return [(tau, 100 * inst_vol(m, tau)) for tau in [0.02 * k for k in range(0, 51)]], q


def kirk_table():
    out = []
    for k in range(0, 21):
        K = -0.5 + 0.1 * k
        c = calendar_spread(K)
        out.append((K, 100 * (c["kirk"] - c["mc"]), 200 * c["se"]))       # cents per MMBtu; 2 s.e.
    return out
