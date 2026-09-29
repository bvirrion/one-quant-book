"""Reference data and symbology services (One Quant Book 15, chapter 6).

A synthetic universe over 500 trading days: 100 listings at the start and 10 new ones later, each with a permanent
external key (its ISIN), a ticker, a name, a lot size and a tick; 12 ticker changes, 5 of whose old tickers go later
to a new listing (as the META ticker passed from an ETF to a company in 2022); 20 splits, each announced 10 to 30 days
before it takes effect, one of them later cancelled. Two vendors deliver the facts: vendor A promptly, but with one lot
size mistyped for six days; vendor B learns two ticker changes two days late, and one rename only three days after its
old ticker was reused by a new listing. A corporate-action feed announces each split, confirms it three days
later, or cancels it. The reference-data service (firm.refdata) builds a golden copy (A first for lot, tick
and ticker, B first for the name) and resolves tickers point in time. A ticker-keyed backtest of a basket of 20
tickers chosen on day 0 is run with today's mapping and unadjusted prices, and point in time with split adjustment.
"""
from __future__ import annotations

import functools
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "refdata"))
from firm_refdata import CounterpartyMaster, RefData  # noqa: E402

DAYS = 500
PRECEDENCE = {"lot": ("A", "B"), "tick": ("A", "B"), "ticker": ("A", "B"), "name": ("B", "A")}


@dataclass
class Universe:
    isin: list            # external key per listing index
    start: np.ndarray     # first day listed
    ticker_changes: list  # (listing, day, new ticker)
    reused: list          # (listing, day, ticker) new listings taking an old ticker
    splits: list          # (event, listing, announced, effective, ratio, cancelled_day or None)
    tickers0: dict        # listing -> first ticker
    prices: np.ndarray    # days x listings, nan before listing


def _name(i):
    return f"L{i:03d}"


@functools.lru_cache(maxsize=4)
def universe(seed: int = 6) -> Universe:
    rng = np.random.default_rng(seed)
    n0, n_new = 100, 10
    n = n0 + n_new
    isin = [f"XS{100000000 + i:09d}{i % 10}" for i in range(n)]
    start = np.r_[np.zeros(n0, dtype=int), np.sort(rng.integers(60, 400, n_new))]
    tickers0 = {i: f"T{i:03d}" for i in range(n0)}
    changers = rng.choice(n0, 12, replace=False)
    change_days = np.sort(rng.integers(20, 300, 12))
    ticker_changes = [(int(i), int(d), f"N{i:03d}") for i, d in zip(changers, change_days, strict=True)]
    reused = []
    for k, (i, d, _new) in enumerate(ticker_changes[:5]):          # five old tickers go to the new listings
        j = n0 + k
        start[j] = max(int(start[j]), d + int(rng.integers(5, 40)))
        reused.append((j, int(start[j]), tickers0[i]))
    for k in range(5, n_new):
        tickers0[n0 + k] = f"Z{n0 + k:03d}"
    for j, _d, t in reused:
        tickers0[j] = t
    splits = []
    who = rng.choice(n0, 20, replace=False)
    for e, i in enumerate(who):
        eff = int(rng.integers(40, DAYS - 10))
        ann = eff - int(rng.integers(10, 31))
        ratio = float(rng.choice([2.0, 3.0, 4.0]))
        splits.append((f"CA{e:02d}", int(i), ann, eff, ratio, ann + 5 if e == 19 else None))
    rets = rng.normal(0.0003, 0.02, (DAYS, n))
    logp = np.cumsum(rets, axis=0) + np.log(rng.uniform(20, 200, n))
    prices = np.exp(logp)
    for _e, i, _a, eff, ratio, cancelled in splits:
        if cancelled is None:
            prices[eff:, i] /= ratio
    for j in range(n):
        prices[: start[j], j] = np.nan
    return Universe(isin, start, ticker_changes, reused, splits, tickers0, prices)


def truth_ticker(u: Universe, i: int, day: int):
    if day < u.start[i]:
        return None
    t = u.tickers0[i]
    for j, d, new in u.ticker_changes:
        if j == i and d <= day:
            t = new
    return t


def build(u: Universe | None = None) -> tuple[RefData, dict]:
    """Deliver both vendors' facts into a reference-data service; return it and the planted defects."""
    u = u or universe()
    rd = RefData(PRECEDENCE)
    late_b_changes = {c[0] for c in u.ticker_changes[:3]}
    typo = (7, 100, 105)                                          # listing, first and last day A is wrong
    j0, reuse_day, _t = u.reused[0]                               # B learns the first reuse three days late:
    i0 = u.ticker_changes[0][0]                                   # the old holder keeps the ticker in B until then
    for i, key in enumerate(u.isin):
        s = int(u.start[i])
        for v in ("A", "B"):
            rd.ingest(v, s + (3 if (v, i) == ("B", j0) else 0), s, key, "ticker", u.tickers0[i])
            rd.ingest(v, s, s, key, "name", f"Company {_name(i)}" if v == "B" else f"COMPANY {_name(i)} INC")
            rd.ingest(v, s, s, key, "tick", 0.01)
            rd.ingest(v, s, s, key, "lot", 100)
    for i, d, new in u.ticker_changes:
        rd.ingest("A", d, d, u.isin[i], "ticker", new)
        known_b = reuse_day + 3 if i == i0 else d + (2 if i in late_b_changes else 0)
        rd.ingest("B", known_b, d, u.isin[i], "ticker", new)
    i, a, b = typo
    rd.ingest("A", a, a, u.isin[i], "lot", 10)
    rd.ingest("A", b + 1, a, u.isin[i], "lot", 100)             # the correction: a new version of the same fact
    for e, i, ann, eff, ratio, cancelled in u.splits:              # the corporate-action feed: announced, then
        pid = rd.pid(u.isin[i])                                     # confirmed three days later, or cancelled
        rd.add_action(e, pid, "split", ratio, eff, "announced", ann)
        rd.add_action(e, pid, "split", ratio, eff, "cancelled" if cancelled is not None else "confirmed",
                      cancelled if cancelled is not None else ann + 3)
    return rd, {"typo": typo, "late_b_changes": late_b_changes,
                "first_reuse": (j0, reuse_day, i0)}


def golden_quality(rd: RefData, u: Universe, field: str = "ticker") -> dict:
    """Instrument-days (as known each day) on which vendor A alone, vendor B alone and the golden copy differ from the
    truth for `field` ('ticker' or 'lot'), and the days a conflict between the vendors was reported."""
    bad = {"A": 0, "B": 0, "golden": 0, "conflict": 0}
    total = 0
    for i, key in enumerate(u.isin):
        pid = rd.pid(key)
        for day in range(int(u.start[i]), DAYS):
            t = truth_ticker(u, i, day) if field == "ticker" else 100
            a, b = rd.value("A", pid, field, day, day), rd.value("B", pid, field, day, day)
            total += 1
            bad["A"] += a != t
            bad["B"] += b != t
            bad["golden"] += rd.golden(pid, field, day, day)[0] != t
            bad["conflict"] += a is not None and b is not None and a != b
    return {"instrument_days": total, **bad}


def mapping_differs(rd: RefData, u: Universe) -> dict:
    """Ticker-days on which resolving by today's (last day's) mapping names a different listing than point in time."""
    last = DAYS - 1
    tickers = sorted({truth_ticker(u, i, d) for i in range(len(u.isin)) for d in (0, last)} - {None})
    diff = total = 0
    for t in tickers:
        today = rd.resolve("ticker", t, last, last)
        for day in range(0, DAYS, 5):
            pit = rd.resolve("ticker", t, day, day)
            if pit:
                total += 1
                diff += pit != today
    return {"ticker_days": total, "differ": diff, "share": diff / total}


def basket_backtest(rd: RefData, u: Universe, k: int = 20, seed: int = 4) -> dict:
    """Buy-and-hold return of an equal-weight basket of k tickers chosen on day 0, three ways: the truth (the
    intended listings, split-adjusted), today's mapping with unadjusted prices, and point in time with factors."""
    rng = np.random.default_rng(seed)
    universe_0 = [i for i in range(len(u.isin)) if u.start[i] == 0]
    changed = [c[0] for c in u.ticker_changes[:5]]
    split_names = [s[1] for s in u.splits if s[5] is None][:6]
    pool = [i for i in universe_0 if i not in changed + split_names]
    chosen = changed + split_names + list(rng.choice(pool, k - len(changed) - len(split_names), replace=False))
    tickers = [truth_ticker(u, i, 0) for i in chosen]
    last = DAYS - 1

    def ret(i, adjust, known):
        pid = rd.pid(u.isin[i])
        f = rd.factor(pid, 0, last, known) if adjust else 1.0
        return u.prices[last, i] * f / u.prices[0, i] - 1.0

    truth = float(np.mean([ret(i, True, last) for i in chosen]))
    naive_rets = []
    for t in tickers:
        now = rd.resolve("ticker", t, last, last)
        if now:
            j = [x for x in range(len(u.isin)) if rd.pid(u.isin[x]) == now[0]][0]
            p0 = u.prices[int(u.start[j]), j]            # the reused ticker's listing has no day-0 price
            naive_rets.append(u.prices[last, j] / p0 - 1.0)
        else:
            naive_rets.append(0.0)                         # the ticker no longer exists today: position dropped
    pit = []
    for t in tickers:
        pid = rd.resolve("ticker", t, 0, 0)[0]
        i = [x for x in range(len(u.isin)) if rd.pid(u.isin[x]) == pid][0]
        pit.append(ret(i, True, last))
    unadj = np.mean([ret(i, False, last) for i in chosen])
    today_adj = []
    for t in tickers:
        now = rd.resolve("ticker", t, last, last)
        if now:
            j = [x for x in range(len(u.isin)) if rd.pid(u.isin[x]) == now[0]][0]
            f = rd.factor(now[0], int(u.start[j]), last, last)
            today_adj.append(u.prices[last, j] * f / u.prices[int(u.start[j]), j] - 1.0)
        else:
            today_adj.append(0.0)
    return {"truth": truth, "naive": float(np.mean(naive_rets)), "pit": float(np.mean(pit)),
            "right_names_unadjusted": float(unadj), "today_mapping_adjusted": float(np.mean(today_adj)),
            "tickers": tickers, "n_changed": len(changed),
            "n_split": len(split_names)}


def counterparties() -> CounterpartyMaster:
    cm = CounterpartyMaster()
    cm.add("LEI-HOLD", "Holding plc", None, 0, 0)
    cm.add("LEI-BANK", "Bank AG", "LEI-HOLD", 0, 0)
    cm.add("LEI-FUND", "Fund LP", None, 0, 0)
    cm.add("LEI-FUND", "Fund LP", "LEI-BANK", 250, 260)           # acquired on day 250, known on day 260
    return cm


def conflicts_by_day(rd: RefData, u: Universe) -> list[int]:
    """Number of instruments whose two vendors disagree on the ticker, each day, as known that day."""
    return [len(rd.conflicts("ticker", day, day)) for day in range(DAYS)]
