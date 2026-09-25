"""Universe, symbology and corporate actions (One Quant Book 7, chapter 4).

A simulated market of listings over ten years, month by month: listings and delistings (for performance,
with a -30% delisting return, and by cash merger, at a premium), splits when a price gets high, ticker
changes, and tickers freed by delisted companies reused by new ones. From it: a security master; a
liquidity universe with and without a buffer; a ticker-keyed price file and the histories it splices;
and a price floor applied to split-adjusted prices. NumPy only.
"""
from __future__ import annotations

import math
import pathlib
import string
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3] / "firm" / "secmaster"))
from firm_secmaster import SecurityMaster, buffered_universe, churn  # noqa: E402

MONTHS = 120


def _tickers(rng):
    """An endless supply of fresh three- and four-letter tickers, in random order."""
    letters = np.array(list(string.ascii_uppercase))
    seen = set()
    while True:
        t = "".join(rng.choice(letters, int(rng.integers(3, 5))))
        if t not in seen:
            seen.add(t)
            yield t


def market(n0: int = 1000, seed: int = 4, reuse_prob: float = 0.35, reuse_lag: int = 1, rename_rate: float = 0.002,
           merger_rate: float = 0.003, barrier: float = -1.6, delist_ret: float = -0.30, premium: float = 0.25):
    """Simulate the listing history. Returns dict with the security master, monthly total returns and
    closes by permanent id (NaN when not listed), split events, and each listing's shares outstanding."""
    rng = np.random.default_rng(seed)
    fresh = _tickers(rng)
    sm = SecurityMaster()
    T, cap = MONTHS, 3 * n0
    ret = np.full((T, cap), np.nan)
    close = np.full((T, cap), np.nan)
    shares = np.full((T, cap), np.nan)
    splits = []                                    # (month, pid, ratio)
    freed = []                                     # (month freed, ticker)
    alive = {}                                     # pid -> [price, cum log return, vol, shares]
    nxt = 0

    def new_listing(t):
        nonlocal nxt
        pool = [k for k, (m, _) in enumerate(freed) if t - m >= reuse_lag]
        if pool and rng.random() < reuse_prob:
            k = pool[int(rng.integers(len(pool)))]
            tick = freed.pop(k)[1]
        else:
            tick = next(fresh)
        pid = nxt
        nxt += 1
        sm.list(pid, tick, t)
        alive[pid] = [float(rng.uniform(8.0, 60.0)), 0.0, float(rng.uniform(0.07, 0.15)),
                      float(math.exp(rng.normal(math.log(50e6), 0.9)))]
        return pid

    for _ in range(n0):
        new_listing(0)
    for t in range(T):
        mkt = rng.normal(0.006, 0.045)
        for pid in list(alive):
            p, cum, vol, sh = alive[pid]
            if t == sm._start[pid]:
                close[t, pid], shares[t, pid] = p, sh
                continue
            r = math.exp(mkt + rng.normal(0.002 - 0.5 * vol * vol, vol)) - 1.0
            cum += math.log1p(r)
            if cum < barrier:                                     # performance delisting
                ret[t, pid] = delist_ret
                sm.delist(pid, t, "performance", delist_ret)
                freed.append((t, sm.ticker(pid, t)))
                del alive[pid]
                continue
            if rng.random() < merger_rate:                       # cash merger at a premium
                ret[t, pid] = (1 + r) * (1 + premium) - 1
                sm.delist(pid, t, "merger", ret[t, pid])
                freed.append((t, sm.ticker(pid, t)))
                del alive[pid]
                continue
            p *= 1 + r
            ret[t, pid] = r
            if p > 200.0:                                         # a split brings the price back down
                ratio = 3 if p > 400.0 else 2
                p, sh = p / ratio, sh * ratio
                splits.append((t, pid, ratio))
            if rng.random() < rename_rate:
                sm.rename(pid, next(fresh), t)
            close[t, pid], shares[t, pid] = p, sh
            alive[pid] = [p, cum, vol, sh]
        while len(alive) < n0:
            new_listing(t)
    n = nxt
    return {"sm": sm, "ret": ret[:, :n], "close": close[:, :n], "shares": shares[:, :n], "splits": splits, "n": n}


def split_factor_today(m) -> np.ndarray:
    """Cumulative split factor from each month to the end of the sample, per listing: the vendor's
    back-adjustment divides past prices by the product of the later split ratios."""
    T, n = m["close"].shape
    f = np.ones((T, n))
    for t, pid, ratio in m["splits"]:
        f[: t, pid] *= ratio              # prices before the split month are divided by the ratio
    return f


def ticker_file(m) -> dict:
    """A price file keyed by ticker, as a careless loader builds it: each ticker's monthly closes in date
    order, whoever held it (split-adjusted within each holder, delisting returns absent)."""
    sm, close = m["sm"], m["close"] / split_factor_today(m)
    by_t: dict[str, list] = {}
    for pid in range(m["n"]):
        for start, end, tick in sm.spans(pid):
            last = MONTHS - 1 if end is None else min(end, MONTHS - 1)
            for t in range(start, last + 1):
                if not math.isnan(close[t, pid]):
                    by_t.setdefault(tick, []).append((t, pid, close[t, pid]))
    return {k: sorted(v) for k, v in by_t.items()}


def ticker_panel(m) -> tuple[list, np.ndarray, dict]:
    """The ticker-keyed table: one column per ticker, monthly returns computed from consecutive closes in the
    ticker file whoever held it, and counts of the spurious returns that span two different listings."""
    tf = ticker_file(m)
    names = sorted(tf)
    col = {k: j for j, k in enumerate(names)}
    out = np.full((MONTHS, len(names)), np.nan)
    spurious = []
    for k, rows in tf.items():
        for (_, p0, c0), (t1, p1, c1) in zip(rows, rows[1:], strict=False):
            out[t1, col[k]] = c1 / c0 - 1.0
            if p0 != p1:
                spurious.append(c1 / c0 - 1.0)
    a = np.abs(spurious)
    return names, out, {"n_spurious": len(spurious), "mean_abs_spurious": float(a.mean()) if len(a) else 0.0,
                        "median_abs_spurious": float(np.median(a)) if len(a) else 0.0}


def ticker_universe(m, uni: dict, names: list) -> dict:
    """The same universe, expressed in tickers: the tickers its members had at each month."""
    col = {k: j for j, k in enumerate(names)}
    sm = m["sm"]
    return {t: {col[sm.ticker(pid, t)] for pid in mem} for t, mem in uni.items()}


def dollar_volume(m) -> np.ndarray:
    """A liquidity score known at each month: price times shares outstanding times a turnover draw."""
    rng = np.random.default_rng(99)
    return m["close"] * m["shares"] * np.exp(rng.normal(0, 0.3, m["close"].shape))


def universe(m, n: int = 500, exit_rank: int | None = None) -> dict:
    dv = dollar_volume(m)

    def scores(t):
        row = dv[t]
        return {int(i): float(row[i]) for i in np.flatnonzero(~np.isnan(row))}

    return buffered_universe(range(MONTHS), scores, n, exit_rank)


def spliced_windows(m, uni: dict, names: list, lookback: int = 12) -> float:
    """Share of (month, universe ticker) pairs whose trailing `lookback`-month return window in the ticker
    table mixes two listings: the history a ticker-keyed signal reads is partly another company's."""
    tf = ticker_file(m)
    holders = {k: {t: pid for t, pid, _ in rows} for k, rows in tf.items()}
    tick_uni = ticker_universe(m, uni, names)
    hit = total = 0
    for t in range(lookback, MONTHS):
        for j in tick_uni[t]:
            h = holders[names[j]]
            pids = {h[s] for s in range(t - lookback, t + 1) if s in h}
            total += 1
            hit += len(pids) > 1
    return hit / total


def ann(x) -> float:
    return float(np.mean(x) * 12)


def price_filter_leak(m, floor: float = 5.0):
    """Months x names where a price floor applied to split-adjusted prices disagrees with the floor on the
    prices that traded; and the next-twelve-month return of the names it wrongly drops."""
    adj = m["close"] / split_factor_today(m)
    raw = m["close"]
    wrong_out = (raw >= floor) & (adj < floor)
    T = raw.shape[0]
    lr = np.nan_to_num(np.log1p(m["ret"]))
    fwd = np.full_like(raw, np.nan)
    for t in range(T - 12):
        fwd[t] = np.expm1(lr[t + 1: t + 13].sum(axis=0))
    listed = raw >= floor
    ok = ~np.isnan(fwd)
    return {"share_wrong": float(wrong_out.sum() / listed.sum()),
            "fwd_wrong": float(np.nanmean(fwd[wrong_out & ok])), "fwd_all": float(np.nanmean(fwd[listed & ok])),
            "n_split_names": len({pid for _, pid, _ in m["splits"]})}


def summary(seed: int = 4):
    m = market(seed=seed)
    sm = m["sm"]
    reused = sm.reused()
    uni = universe(m, 500, 600)
    names, _, spur = ticker_panel(m)
    delist = [sm.delisting(p) for p in range(m["n"]) if sm.delisting(p)]
    return {
        "listings": m["n"], "delistings": len(delist),
        "performance": sum(1 for d in delist if d[1] == "performance"),
        "mergers": sum(1 for d in delist if d[1] == "merger"),
        "splits": len(m["splits"]), "reused_tickers": len(reused), "spurious": spur,
        "churn_plain": churn(universe(m, 500)), "churn_buffer": churn(uni),
        "spliced_windows": spliced_windows(m, uni, names), "tickers": len(names),
        "leak": price_filter_leak(m),
    }
