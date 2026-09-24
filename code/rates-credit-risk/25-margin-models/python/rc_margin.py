"""Chapter 25 of Book 6: margin models on a member's cleared USD swap book, with daily US Treasury par
yields standing in for swap rates. Exposures in USD per basis point by tenor (illustrative): +60k at two
years, -40k at five, -150k at ten, -30k at thirty (P&L for a one-basis-point rise). Initial margin by
historical simulation (five-day moves, 99%, one-year look-back), by filtered historical simulation, by a
sensitivity-based model with illustrative risk weights, and by the standardised schedule; a replay of
January-June 2020 with and without anti-procyclicality tools; and a backtest since 2017."""
import csv
import datetime as dt
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/initmargin"))
from firm_initmargin import (  # noqa: E402
    apc_buffer,
    apc_stressed_weight,
    backtest,
    ewma_vol,
    fhs_moves,
    hs_im,
    overlapping,
    schedule_im,
    simm_like,
)

TENORS = [2.0, 5.0, 10.0, 30.0]
COLS = ["y2", "y5", "y10", "y30"]
EXPOSURE = np.array([60e3, -40e3, -150e3, -30e3])          # USD per bp rise, by tenor
H, LOOKBACK, Q = 5, 250, 0.99
RW_BP = [60.0, 60.0, 55.0, 50.0]                            # illustrative ten-day risk weights, bp


def data():
    with open(ROOT / "data/rates-credit-risk/treasury_par_yields.csv") as fh:
        rows = [r for r in csv.DictReader(fh) if all(r[c] for c in COLS)]
    dates = [dt.date.fromisoformat(r["date"]) for r in rows]
    lv = np.array([[float(r[c]) * 100 for c in COLS] for r in rows])          # in bp
    return dates, np.diff(lv, axis=0), dates[1:]


def pnl(moves_bp: np.ndarray) -> np.ndarray:
    return moves_bp @ EXPOSURE


def im_series(start: dt.date, end: dt.date) -> dict:
    """Daily IM from `start` to `end` (inclusive) by HS and FHS, each from data up to the day."""
    _, x, d = data()
    out = {"date": [], "hs": [], "fhs": []}
    for t, day in enumerate(d):
        if day < start or day > end:
            continue
        win = x[t + 1 - LOOKBACK - H + 1:t + 1]
        out["date"].append(day)
        out["hs"].append(hs_im(pnl(overlapping(win, H)), Q))
        out["fhs"].append(hs_im(pnl(fhs_moves(x[t + 1 - 2 * LOOKBACK:t + 1], H)[-LOOKBACK:]), Q))
    for k in ("hs", "fhs"):
        out[k] = np.array(out[k])
    return out


def stress_flags(dates, start: dt.date) -> np.ndarray:
    """Stress when the EWMA volatility of the portfolio P&L is above twice its one-year average."""
    _, x, d = data()
    p = pnl(x)[:, None]
    v, _ = ewma_vol(p, 0.97)
    idx = {day: i for i, day in enumerate(d)}
    flags = []
    for day in dates:
        i = idx[day]
        flags.append(v[i, 0] > 2.0 * v[i - LOOKBACK:i, 0].mean())
    return np.array(flags)


def stressed_im() -> float:
    """HS IM of the most stressed one-year window before 2020."""
    _, x, d = data()
    k = next(i for i, day in enumerate(d) if day.year >= 2020)
    best = 0.0
    for s in range(0, k - LOOKBACK, 5):
        best = max(best, hs_im(pnl(overlapping(x[s:s + LOOKBACK], H)), Q))
    return best


def replay_2020() -> dict:
    s = im_series(dt.date(2020, 1, 2), dt.date(2020, 6, 30))
    feb = np.array([d.month == 2 for d in s["date"]])
    flags = stress_flags(s["date"], dt.date(2020, 1, 2))
    fhs = s["fhs"]
    buf = apc_buffer(fhs, flags, 0.25)
    sw = apc_stressed_weight(fhs, stressed_im(), 0.25)
    out = {"series": s, "flags": flags, "buffer": buf, "stressed": sw, "stressed_im": stressed_im()}
    for k, v in (("hs", s["hs"]), ("fhs", fhs), ("buffer", buf), ("stressed", sw)):
        base = v[feb].mean()
        out[k + "_feb"] = base
        out[k + "_peak"] = float(v.max())
        out[k + "_increase"] = float(v.max() - base)
        out[k + "_ratio"] = float(v.max() / base)
        out[k + "_peakday"] = s["date"][int(v.argmax())].isoformat()
    return out


def simm_today() -> float:
    return simm_like(EXPOSURE, TENORS, RW_BP)


def hs10_today() -> float:
    _, x, _ = data()
    return hs_im(pnl(overlapping(x[-LOOKBACK - 9:], 10)), Q)


def schedule_today(ngr: float = 0.5) -> dict:
    dur = {2.0: 1.9, 5.0: 4.5, 10.0: 8.0, 30.0: 16.0}          # illustrative swap durations
    trades = [("ir", e / (dur[t] * 1e-4), dur[t]) for t, e in zip(TENORS, EXPOSURE, strict=True)]
    return {**schedule_im(trades, ngr, 1.0), "notionals": [n for _, n, _ in trades]}


def backtest_since(start: dt.date = dt.date(2017, 1, 3)) -> dict:
    _, x, d = data()
    n = len(x)
    hits = {"hs": 0, "fhs": 0}
    days = 0
    for t in range(n - H):
        if d[t] < start or t + 1 - 2 * LOOKBACK < 0:
            continue
        loss = -pnl(x[t + 1:t + 1 + H].sum(axis=0)[None, :])[0]
        hs = hs_im(pnl(overlapping(x[t + 1 - LOOKBACK - H + 1:t + 1], H)), Q)
        fh = hs_im(pnl(fhs_moves(x[t + 1 - 2 * LOOKBACK:t + 1], H)[-LOOKBACK:]), Q)
        hits["hs"] += backtest(np.array([hs]), np.array([loss]))
        hits["fhs"] += backtest(np.array([fh]), np.array([loss]))
        days += 1
    return {"days": days, **hits}


def dv01_net() -> float:
    return float(EXPOSURE.sum())
