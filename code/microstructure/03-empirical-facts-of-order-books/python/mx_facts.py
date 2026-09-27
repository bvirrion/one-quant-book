"""One Quant Book 10, chapter 3: the empirical facts of order books, measured on the simulated market (firm.tape) and
read from the SEC's MIDAS statistics (derived files in data/microstructure/, written by mx_fetch_midas.py).

    day()                           one simulated 6.5-hour session with a U-shaped intraday profile (cached)
    relative_prices(tape)           distances of new limit orders from the same-side best, and the tail of their law
    cancel_rates(tape, levels)      cancellations per displayed share per second, by distance from the best
    spread_profile(tape)            time-weighted distribution of the spread in ticks
    intraday(tape, bin_s)           volume, trades, messages and mean spread by time-of-day bin
    lifetable(tape, points)         lifetable CDF of the time to cancellation, executions as censoring (MIDAS's method)
    fleeting_share(tape, horizon)   share of added orders cancelled in full within `horizon` seconds
    resilience(tape)                after executions that empty the best level: time until the spread is one tick again
    spread_vs_vol(configs)          mean spread and volatility per trade over simulated markets, and their fit
    midas_lifetimes(), midas_yearly()   the SEC's figures (2026 Q2; yearly 2012-2026)
All simulated numbers are deterministic (fixed seeds).
"""
from __future__ import annotations

import csv
import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "tape"))
from firm_tape import TapeConfig, simulate  # noqa: E402

DATA = ROOT / "data" / "microstructure"
POINTS = (0.001, 0.01, 0.1, 1.0, 10.0, 60.0)


@functools.lru_cache(maxsize=2)
def day(seed: int = 7, seconds: float = 23_400.0):
    return simulate(TapeConfig(seconds=seconds, u_shape=1.5, seed=seed, news_at=None))


def _replay(tape):
    """Yield (row, best_bid, best_ask) before each message is applied, and keep a book of displayed sizes."""
    levels = {1: {}, -1: {}}
    orders: dict[int, list] = {}
    for row in tape.msgs:
        b = max(levels[1]) if levels[1] else None
        a = min(levels[-1]) if levels[-1] else None
        yield row, b, a, levels
        oid, side, px, q = int(row["oid"]), int(row["side"]), int(row["price"]), int(row["qty"])
        lv = levels[side]
        if row["kind"] == b"A":
            orders[oid] = [side, px, q]
            lv[px] = lv.get(px, 0) + q
        else:
            o = orders[oid]
            o[2] -= q
            lv[o[1]] -= q
            if lv[o[1]] == 0:
                del lv[o[1]]
            if o[2] == 0:
                del orders[oid]


def relative_prices(tape) -> dict:
    """Distance (ticks) of each new limit order from the best price on its own side, positive = behind the best,
    negative = improving it; and the share of orders placed at least k ticks behind."""
    d = []
    for row, b, a, _ in _replay(tape):
        if row["kind"] != b"A" or b is None or a is None:
            continue
        px = int(row["price"])
        d.append(b - px if row["side"] == 1 else px - a)
    d = np.array(d)
    tail = {k: float(np.mean(d >= k)) for k in (1, 2, 4, 8)}
    return {"n": len(d), "improve": float(np.mean(d < 0)), "at_best": float(np.mean(d == 0)), "tail": tail,
            "max": int(d.max())}


def cancel_rates(tape, levels: int = 6) -> np.ndarray:
    """Cancellations per displayed share per second at k = 0..levels-1 ticks behind the best (both sides pooled):
    cancelled shares at distance k divided by the time integral of displayed shares at distance k."""
    canc = np.zeros(levels)
    expo = np.zeros(levels)
    last_t = 0.0
    for row, b, a, lv in _replay(tape):
        t = float(row["t"])
        dt = t - last_t
        last_t = t
        if b is not None and a is not None and dt > 0:
            for k in range(levels):
                expo[k] += (lv[1].get(b - k, 0) + lv[-1].get(a + k, 0)) * dt
        if row["kind"] == b"X" and b is not None and a is not None:
            px = int(row["price"])
            k = b - px if row["side"] == 1 else px - a
            if 0 <= k < levels:
                canc[k] += int(row["qty"])
    return canc / expo


def spread_profile(tape) -> dict:
    top = tape.top[tape.n_open:]
    s = top["ask"] - top["bid"]
    dt = np.diff(np.concatenate([top["t"], [tape.cfg.seconds]]))
    tot = dt.sum()
    return {"one": float(dt[s == 1].sum() / tot), "two": float(dt[s == 2].sum() / tot),
            "three_plus": float(dt[s >= 3].sum() / tot), "mean": float((s * dt).sum() / tot)}


def intraday(tape, bin_s: float = 1800.0) -> list[dict]:
    top = tape.top[tape.n_open:]
    s = top["ask"] - top["bid"]
    dt = np.diff(np.concatenate([top["t"], [tape.cfg.seconds]]))
    out = []
    for lo in np.arange(0.0, tape.cfg.seconds, bin_s):
        hi = lo + bin_s
        tr = tape.trades[(tape.trades["t"] >= lo) & (tape.trades["t"] < hi)]
        m = (top["t"] >= lo) & (top["t"] < hi)
        msgs = int(np.sum((tape.msgs["t"] >= lo) & (tape.msgs["t"] < hi)))
        out.append({"start": lo, "volume": int(tr["qty"].sum()), "trades": len(tr), "messages": msgs,
                    "spread": float((s[m] * dt[m]).sum() / dt[m].sum())})
    return out


def lifetable(tape, points=POINTS, event: bytes = b"X") -> list[float]:
    """Kaplan-Meier CDF of the time from an order's arrival (or last partial event) to a cancellation (event b"X"),
    with executions censoring, as the SEC's MIDAS computes it (the timer restarts after each partial event);
    event b"E" gives the time to execution with cancellations censoring."""
    since: dict[int, float] = {}
    events = []                                   # (duration, cancelled?)
    for row in tape.msgs:
        oid, t = int(row["oid"]), float(row["t"])
        if row["kind"] == b"A":
            since[oid] = t
            continue
        events.append((t - since[oid], row["kind"] == event))
        since[oid] = t
    dur = np.array([d for d, _ in events])
    cens = np.array([not c for _, c in events])
    order = np.argsort(dur, kind="stable")
    dur, cens = dur[order], cens[order]
    n = len(dur)
    at_risk = n - np.arange(n)
    surv = np.cumprod(np.where(cens, 1.0, 1.0 - 1.0 / at_risk))
    return [float(1.0 - (surv[np.searchsorted(dur, p, side="right") - 1] if dur[0] <= p else 1.0)) for p in points]


def fleeting_share(tape, horizon: float = 2.0) -> float:
    added: dict[int, tuple[float, int]] = {}
    left: dict[int, int] = {}
    fleeting = 0
    for row in tape.msgs:
        oid = int(row["oid"])
        if row["kind"] == b"A":
            added[oid], left[oid] = (float(row["t"]), int(row["qty"])), int(row["qty"])
            continue
        left[oid] -= int(row["qty"])
        if left[oid] == 0 and row["kind"] == b"X" and float(row["t"]) - added[oid][0] <= horizon:
            fleeting += 1
    return fleeting / len(added)


def resilience(tape) -> dict:
    """After each trade that empties the best level on its side (the spread widens to two ticks or more): the time
    until the spread is back to one tick; median and share recovered within 1 and 5 seconds."""
    top = tape.top
    s = top["ask"] - top["bid"]
    t = top["t"]
    starts = np.flatnonzero((s[1:] >= 2) & (s[:-1] == 1) & (tape.msgs["kind"][1:] == b"E")) + 1
    rec = []
    for i in starts:
        j = np.flatnonzero(s[i:] == 1)
        if len(j):
            rec.append(t[i + j[0]] - t[i])
    rec = np.array(rec)
    return {"events": len(rec), "median": float(np.median(rec)), "within_1s": float(np.mean(rec <= 1.0)),
            "within_5s": float(np.mean(rec <= 5.0))}


def vol_per_trade(tape) -> tuple[float, float]:
    """(mean spread in ticks, standard deviation of the mid-price change between consecutive trades)."""
    mid = tape.mid()
    idx = np.searchsorted(tape.top["t"], tape.trades["t"], side="right") - 1
    m = mid[np.clip(idx, 0, len(mid) - 1)]
    return spread_profile(tape)["mean"], float(np.std(np.diff(m)))


CONFIGS = [dict(informed=i, v_rate=v, seed=s) for s, (i, v) in enumerate(
    [(0.1, 0.06), (0.25, 0.06), (0.5, 0.06), (0.1, 0.12), (0.25, 0.12), (0.5, 0.12), (0.1, 0.24), (0.25, 0.24),
     (0.5, 0.24), (1.0, 0.24)], start=31)]


def spread_vs_vol(configs=CONFIGS, seconds: float = 1200.0) -> dict:
    pts = []
    for c in configs:
        tp = simulate(TapeConfig(seconds=seconds, news_at=None, **c))
        pts.append(vol_per_trade(tp))
    x = np.array([p[1] for p in pts])
    y = np.array([p[0] for p in pts])
    slope, icpt = np.polyfit(x, y, 1)
    r2 = 1.0 - np.sum((y - (slope * x + icpt)) ** 2) / np.sum((y - y.mean()) ** 2)
    return {"points": pts, "slope": float(slope), "intercept": float(icpt), "r2": float(r2)}


def midas_lifetimes() -> dict:
    with open(DATA / "midas_lifetimes.csv") as f:
        return {(r["group"], r["event"]): [float(r[k]) for k in ("1ms", "10ms", "100ms", "1s", "10s", "1min")]
                for r in csv.DictReader(f)}


def midas_yearly() -> dict:
    with open(DATA / "midas_yearly.csv") as f:
        return {int(r["year"]): {k: float(v) for k, v in r.items() if k != "year"} for r in csv.DictReader(f)}


def intraday_mean(seeds=range(8), seconds: float = 3900.0, bins: int = 13) -> list[dict]:
    """Intraday profile averaged over several compressed sessions (13 bins stand for the day's half hours): one
    simulated day is dominated by its own activity process; the planted U shape shows only on average."""
    acc = np.zeros((bins, 3))
    for s in seeds:
        tp = simulate(TapeConfig(seconds=seconds, u_shape=1.5, seed=100 + s, news_at=None))
        for k, r in enumerate(intraday(tp, seconds / bins)):
            acc[k] += (r["volume"], r["messages"], r["spread"])
    acc /= len(list(seeds))
    return [{"bin": k, "volume": acc[k, 0], "messages": acc[k, 1], "spread": acc[k, 2]} for k in range(bins)]


ZI_CONFIGS = [(0.25, 1.0, 0.05), (0.5, 1.0, 0.05), (1.0, 1.0, 0.05), (0.25, 2.0, 0.05), (0.5, 2.0, 0.05),
              (1.0, 2.0, 0.05), (0.25, 4.0, 0.1), (1.0, 4.0, 0.02)]


def spread_vs_vol_zi(configs=ZI_CONFIGS, events: int = 100_000) -> dict:
    """The same relation in chapter 1's zero-intelligence market, whose spread is free to vary (alpha, mu, delta)."""
    sys.path.insert(0, str(ROOT / "code" / "microstructure" / "01-the-limit-order-book" / "python"))
    from mx_lob import zi_market
    pts = []
    for a, m, d in configs:
        r = zi_market(events=events, alpha=a, mu=m, delta=d, seed=9)
        pts.append((r["spread"], r["vol_per_trade"]))
    x = np.array([p[1] for p in pts])
    y = np.array([p[0] for p in pts])
    slope, icpt = np.polyfit(x, y, 1)
    r2 = 1.0 - np.sum((y - (slope * x + icpt)) ** 2) / np.sum((y - y.mean()) ** 2)
    return {"points": pts, "slope": float(slope), "intercept": float(icpt), "r2": float(r2)}
