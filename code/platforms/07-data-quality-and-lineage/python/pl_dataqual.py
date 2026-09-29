"""Data quality and lineage (One Quant Book 15, chapter 7).

One simulated day of the chapter 4 week (its second day: two instruments, about 47,000 events, 9,600 quotes and 1,200
trades) is taken as clean, and defects are planted in a copy with a seeded generator: a gap of 200 events, three crossed
quotes, eight trade prices off by a factor of ten (a decimal slip, one way or the other), a 90-second silence of one
instrument's quotes, four trades that the venue breaks after the close, and a vendor's later correction of an official
close. firm.dataqual's rule suite runs over the defective copy; each rule's detection and false-flag counts are
measured over twenty seeds of planting; the day's volatility and VWAP are computed with defects kept, with the flagged
rows excluded, and on the clean day.
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/dataqual"))
sys.path.insert(0, str(ROOT / "code/firm/pit"))
sys.path.insert(0, str(ROOT / "code/platforms/04-a-tick-store-on-open-formats/python"))
from firm_dataqual import Lineage, Quarantine, Rule, clean, run  # noqa: E402
from firm_pit import Store  # noqa: E402
from pl_tickstore import SYMBOLS, day_events, quotes_trades  # noqa: E402

SEC = 10**9


@functools.lru_cache(maxsize=4)
def base(day: int = 1, hours: float = 0.1667, gen: str | None = None):
    """The clean day, with two genuine market events that a naive rule mistakes for defects: SIM2's trading is halted
    for 60 seconds at 40% of the session (no quotes, no trades), and SIM2's price level jumps by 3% at 60% of it (news),
    and stays there. Returns (events, quotes, trades, halts)."""
    kw = {"gen": pathlib.Path(gen)} if gen else {}
    ev = day_events(day, hours, **kw)
    q, t = quotes_trades(ev, SYMBOLS)
    q, t = q.to_pandas(), t.to_pandas()
    events = pd.DataFrame({"seq": ev["seq"].astype(np.int64), "ts": ev["ts"].astype(np.int64),
                           "locate": ev["locate"].astype(np.int64)})
    t0, t1 = int(q["ts"].min()), int(q["ts"].max())
    h0 = t0 + int(0.4 * (t1 - t0))
    halts = (("SIM2", h0, h0 + 60 * SEC),)
    q = q[~((q["symbol"] == "SIM2") & (q["ts"] > h0) & (q["ts"] < h0 + 60 * SEC))].copy()
    t = t[~((t["symbol"] == "SIM2") & (t["ts"] > h0) & (t["ts"] < h0 + 60 * SEC))].copy()
    jump = t0 + int(0.6 * (t1 - t0))
    for df, cols in ((q, ("bid", "ask")), (t, ("price",))):
        m = (df["symbol"] == "SIM2") & (df["ts"] >= jump)
        for c in cols:
            df.loc[m, c] = (df.loc[m, c] * 1.03 / 100).round().astype(np.int64) * 100
    return events, q.reset_index(drop=True), t.reset_index(drop=True), halts


def plant(seed: int, day: int = 1, hours: float = 0.1667, gen: str | None = None):
    """Defective copies of the day's tables and the truth: {(table, row): kind} of the rows that carry a defect."""
    events, q, t, _halts = base(day, hours, gen)
    events, q, t = events.copy(), q.copy(), t.copy()
    rng = np.random.default_rng(seed)
    truth = {}
    g0 = int(rng.integers(len(events) // 5, 4 * len(events) // 5))
    lo, hi = int(events["seq"].iloc[g0]), int(events["seq"].iloc[g0]) + 200
    events = events[(events["seq"] < lo) | (events["seq"] >= hi)]
    q = q[(q["seq"] < lo) | (q["seq"] >= hi)]
    t = t[(t["seq"] < lo) | (t["seq"] >= hi)]
    truth[("events", int(events.index[events["seq"] >= hi][0]))] = "gap"
    sim1 = q[q["symbol"] == "SIM1"]
    s0 = int(sim1["ts"].iloc[len(sim1) // 3])
    silent = q.index[(q["symbol"] == "SIM1") & (q["ts"] > s0) & (q["ts"] <= s0 + 90 * SEC)]
    q = q.drop(index=silent)
    after = q.index[(q["symbol"] == "SIM1") & (q["ts"] > s0 + 90 * SEC)]
    if len(after):
        truth[("quotes", int(after[0]))] = "stale"
    for i in rng.choice(q.index, 3, replace=False):
        q.loc[i, "bid"] = q.loc[i, "ask"] + 100
        truth[("quotes", int(i))] = "crossed"
    spikes = rng.choice(t.index[5:-5], 8, replace=False)
    for k, i in enumerate(spikes):
        t.loc[i, "price"] = t.loc[i, "price"] * 10 if k % 2 == 0 else t.loc[i, "price"] // 10
        truth[("trades", int(i))] = "spike"
    others = t.loc[~t.index.isin(spikes), "match"].to_numpy()
    busted = [int(x) for x in rng.choice(others, 4, replace=False)]
    for i in t.index[t["match"].isin(busted)]:
        truth[("trades", int(i))] = "busted"
    return {"events": events, "quotes": q, "trades": t}, truth, busted


def rules(reference_trades: pd.DataFrame, busted: list, halts=(), aware=True) -> dict:
    """The suite. aware=False is the first version: the spike rule does not check that a
    jump comes back, and the staleness rule does not know about trading halts."""
    md, big = "market data", 10**9
    return {
        "events": [Rule("sequence", "sequence", "error", md, {"column": "seq"})],
        "quotes": [Rule("positive prices", "bounds", "error", md,
                        {"column": "bid", "lo": 1, "hi": big}),
                   Rule("crossed book", "crossed", "error", md, {"bid": "bid", "ask": "ask"}),
                   Rule("stale quotes", "stale", "warning", md,
                        {"time": "ts", "max_gap": 30 * SEC, "by": "symbol",
                         "exempt": halts if aware else ()})],
        "trades": [Rule("positive trades", "bounds", "error", md,
                        {"column": "qty", "lo": 1, "hi": big}),
                   Rule("price spike", "spike", "error", md,
                        {"column": "price", "k": 8.0, "window": 50, "floor": 1e-3,
                         "confirm": aware, "by": "symbol"}),
                   Rule("broken trades", "busted", "error", "operations",
                        {"key": "match", "busted": busted}),
                   Rule("vendor trade count", "cross_source", "warning", md,
                        {"time": "ts", "bucket": 60 * SEC, "tol": 0.02,
                         "reference": reference_trades})],
    }


KIND_OF_RULE = {"sequence": "gap", "crossed book": "crossed", "price spike": "spike", "stale quotes": "stale",
                "broken trades": "busted"}


def score(seed: int, aware: bool = True, **kw) -> dict:
    tables, truth, busted = plant(seed, **kw)
    _e, _q, ref, halts = base(**{k: v for k, v in kw.items() if k in ("day", "hours", "gen")})
    flags = run(rules(ref, busted, halts, aware), tables)
    out = {}
    for rule, kind in KIND_OF_RULE.items():
        mine = {(f.table, f.row) for f in flags if f.rule == rule}
        planted = {k for k, v in truth.items() if v == kind}
        out[rule] = {"planted": len(planted), "found": len(planted & mine), "false": len(mine - planted)}
    out["vendor trade count"] = {"flags": sum(f.rule == "vendor trade count" for f in flags)}
    return out


@functools.lru_cache(maxsize=4)
def detection(seeds: int = 20, aware: bool = True, **kw) -> dict:
    total = {}
    for s in range(seeds):
        for rule, d in score(s, aware, **kw).items():
            acc = total.setdefault(rule, {})
            for k, v in d.items():
                acc[k] = acc.get(k, 0) + v
    return total


def realised(trades: pd.DataFrame) -> dict:
    """Per symbol: realised variance of log trade-price changes, and VWAP (price units)."""
    out = {}
    for sym, g in trades.sort_values("seq").groupby("symbol"):
        r = np.diff(np.log(g["price"].to_numpy(dtype=float)))
        out[sym] = {"rv": float((r**2).sum()), "vwap": float((g["price"] * g["qty"]).sum() / g["qty"].sum())}
    return out


def effect(seed: int = 0, **kw) -> dict:
    tables, _truth, busted = plant(seed, **kw)
    _e, _q, ref, halts = base(**{k: v for k, v in kw.items() if k in ("day", "hours", "gen")})
    flags = run(rules(ref, busted, halts), tables)
    t = tables["trades"]
    truth_t = ref[~ref["match"].isin(busted)]
    return {"kept": realised(t), "flagged_out": realised(clean(t, flags, "trades", ("error",))),
            "truth": realised(truth_t)}


def quarantine_demo(seed: int = 0, **kw) -> Quarantine:
    tables, _truth, busted = plant(seed, **kw)
    _e, _q, ref, halts = base(**{k: v for k, v in kw.items() if k in ("day", "hours", "gen")})
    qz = Quarantine()
    qz.apply("trades/date=2026-09-22", run(rules(ref, busted, halts), tables))
    qz.release("trades/date=2026-09-22", "market-data on-call", "gap confirmed by the venue; flags kept")
    return qz


def correction_and_lineage() -> dict:
    """A vendor corrects SIM2's official close; the store keeps both versions and the lineage names what is stale."""
    closes = Store()
    closes.put("SIM2", "close", "2026-09-22", "2026-09-22T16:30", 3_004_500)
    closes.put("SIM2", "close", "2026-09-22", "2026-09-23T07:10", 3_004_300)       # the vendor's correction
    lin = Lineage()
    raw = lin.add("trades 2026-09-22", {"close": 3_004_500})
    fixed_close = lin.add("closes 2026-09-22", {"SIM2": 3_004_500}, [raw])
    marks = lin.add("marks 2026-09-22", {"SIM2": 300.45}, [fixed_close], "eod_marks v3")
    pnl = lin.add("pnl 2026-09-22", {"desk": 1250.0}, [marks], "pnl v7")
    bars = lin.add("bars 2026-09-22", {"n": 390}, [raw], "bars v2")
    feats = lin.add("features 2026-09-22", {"mom": 0.1}, [bars, fixed_close], "features v5")
    stale = lin.stale_after("closes 2026-09-22", fixed_close[1])
    return {"asof_night": closes.asof("SIM2", "close", "2026-09-22", "2026-09-22T23:00"),
            "asof_morning": closes.asof("SIM2", "close", "2026-09-22", "2026-09-23T08:00"),
            "vintages": closes.vintages("SIM2", "close", "2026-09-22"),
            "stale": sorted(n for n, _ in stale), "untouched": sorted(n for n, _ in {bars}),
            "upstream_of_pnl": sorted(n for n, _ in lin.upstream(pnl)), "features": feats[0]}
