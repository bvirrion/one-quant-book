"""Market data for research (One Quant Book 7, chapter 2).

One simulated trading day of message-level data (firm.tape: 6.5 hours, a U-shaped activity profile
and a news burst 12,600 seconds after the open), sampled by four clocks; the volatility a researcher
measures from trades and from midquotes; and a continuous WTI
futures series built three ways from the EIA's nearby and second-month settlements.
"""
from __future__ import annotations

import csv
import datetime as dt
import functools
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve()
FIRM = HERE.parents[3] / "firm"
sys.path.insert(0, str(FIRM / "tape"))
sys.path.insert(0, str(FIRM / "bars"))
from firm_bars import asof, continuous, dollar_bars, tick_bars, time_bars, volume_bars  # noqa: E402
from firm_tape import TapeConfig, simulate  # noqa: E402

DAY = TapeConfig(seconds=23_400.0, u_shape=1.5, news_at=12_600.0, seed=3)
WTI = HERE.parents[4] / "data" / "markets-3" / "wti_futures_c1_c4_daily.csv"


@functools.lru_cache(maxsize=1)
def day():
    return simulate(DAY)


def kurtosis(x) -> float:
    x = np.asarray(x, float) - np.mean(x)
    return float((x**4).mean() / (x**2).mean() ** 2)


def mids(tape):
    top = tape.top[tape.n_open:]
    return top["t"], 0.5 * (top["bid"] + top["ask"])


def realised_variance(tape, width: float) -> tuple[float, float]:
    """Realised variance of log returns on a grid of `width` seconds, from the last trade price and
    from the midquote at each grid time (units of 1e-4, i.e. squared percent)."""
    tt, m = mids(tape)
    tr = tape.trades
    g = np.arange(width, tape.cfg.seconds + 1e-9, width)
    rt = np.diff(np.log(asof(tr["t"], tr["price"], g)))
    rm = np.diff(np.log(asof(tt, m, g)))
    return float((rt**2).sum() * 1e4), float((rm**2).sum() * 1e4)


def clocks(tape, n_bars: int = 390):
    """Time, tick, volume and dollar bars, each with about n_bars bars over the day."""
    tr = tape.trades
    t, px, q = tr["t"], tr["price"] * tape.cfg.tick, tr["qty"].astype(float)
    return {
        "time": time_bars(t, px, q, tape.cfg.seconds / n_bars, 0.0, tape.cfg.seconds),
        "tick": tick_bars(t, px, q, len(t) // n_bars),
        "volume": volume_bars(t, px, q, q.sum() / n_bars),
        "dollar": dollar_bars(t, px, q, (px * q).sum() / n_bars),
    }


def mid_returns(tape, bars) -> np.ndarray:
    """Log midquote returns between bar ends (removes the bounce, keeps the clock)."""
    tt, m = mids(tape)
    return np.diff(np.log(asof(tt, m, bars.end)))


def mixture_kurtosis(volumes) -> float:
    """Kurtosis of a normal variance mixture whose variance is proportional to the bar's volume:
    3 E[V^2] / E[V]^2 = 3 (1 + CV^2)."""
    v = np.asarray(volumes, float)
    return 3.0 * float((v**2).mean() / v.mean() ** 2)


def bars_per_window(bars, window: float, seconds: float) -> np.ndarray:
    edges = np.arange(0.0, seconds + 1e-9, window)
    return np.histogram(bars.end, bins=edges)[0]


def summary():
    tp = day()
    rv = {w: realised_variance(tp, w) for w in (1, 5, 60, 300)}
    c = clocks(tp)
    kurt_close = {k: kurtosis(b.returns()) for k, b in c.items()}
    kurt_mid = {k: kurtosis(mid_returns(tp, b)) for k, b in c.items()}
    return {
        "msgs": len(tp.msgs), "trades": len(tp.trades), "rv": rv,
        "n_bars": {k: len(b) for k, b in c.items()},
        "kurt_close": kurt_close, "kurt_mid": kurt_mid,
        "kurt_mixture_time": mixture_kurtosis(c["time"].volume),
        "msgs_per_trade": len(tp.msgs) / len(tp.trades),
    }


# ---------------------------------------------------------------------------- WTI continuous series

def load_wti(start: str = "2015-01-02", end: str = "2024-04-05"):
    rows = []
    with open(WTI) as fh:
        for r in csv.DictReader(fh):
            if start <= r["date"] <= end:
                rows.append((dt.date.fromisoformat(r["date"]), float(r["c1"]), float(r["c2"])))
    d = [r[0] for r in rows]
    return d, np.array([r[1] for r in rows]), np.array([r[2] for r in rows])


def wti_expiries(dates) -> np.ndarray:
    """Last trading day of the nearby contract: three business days before the 25th calendar day of
    the month before delivery, counted from the last business day preceding the 25th when the 25th is
    not one. Both cases are three business days before the last business day on or before the 25th.
    Business days are the dates on which the EIA publishes settlements (exchange trading days)."""
    flags = np.zeros(len(dates), bool)
    by_month: dict[tuple[int, int], list[int]] = {}
    for i, d in enumerate(dates):
        by_month.setdefault((d.year, d.month), []).append(i)
    for idx in by_month.values():
        upto = [i for i in idx if dates[i].day <= 25]
        complete = dates[idx[-1]].day >= 25 or (idx[-1] + 1 < len(dates))   # the data reach past the 25th
        if upto and complete and upto[-1] - 3 >= 0:
            flags[upto[-1] - 3] = True
    return flags


def wti_series(days_before: int = 5, start: str = "2015-01-02", end: str = "2024-04-05"):
    d, c1, c2 = load_wti(start, end)
    exp = wti_expiries(d)
    out = continuous(c1, c2, exp, days_before)
    out.update({"dates": d, "c1": c1, "c2": c2, "expiry": exp})
    return out


def wti_summary(days_before: int = 5):
    s = wti_series(days_before)
    held_ret = np.diff(np.log(s["held"]))
    roll_next = np.zeros(len(held_ret), bool)
    roll_next[s["rolls"][s["rolls"] < len(held_ret)]] = True        # the return from a roll day to the next
    same_contract = np.log(s["c2"][1:] / s["c2"][:-1])              # held c2 after a roll: its own return
    held_ret_fixed = np.where(roll_next, same_contract, held_ret)
    return {
        "n_days": len(s["dates"]), "n_rolls": len(s["rolls"]),
        "first_c1": float(s["c1"][0]), "last_c1": float(s["c1"][-1]),
        "back_first": float(s["back"][0]), "ratio_first": float(s["ratio"][0]),
        "back_min": float(s["back"].min()), "back_min_date": s["dates"][int(np.argmin(s["back"]))],
        "raw_return": math.log(s["c1"][-1] / s["c1"][0]),
        "ratio_return": math.log(s["ratio"][-1] / s["ratio"][0]),
        "held_return": float(held_ret_fixed.sum()),
        "gap_sum": float(sum(s["c2"][r] - s["c1"][r] for r in s["rolls"])),
        "worst_gap": float(max(s["c2"][r] - s["c1"][r] for r in s["rolls"])),
        "worst_gap_date": s["dates"][int(max(s["rolls"], key=lambda r: s["c2"][r] - s["c1"][r]))],
        "c1_min": float(s["c1"].min()), "held_min": float(s["held"].min()),
    }
