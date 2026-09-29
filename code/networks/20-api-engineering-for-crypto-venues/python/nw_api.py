"""Chapter 20 of One Quant Book 14: shards, resynchronisation, rate budgets and venue clocks (firm.cryptofeed on
Book 3's firm.ratelimit and firm.wsbook).

    SYMBOLS, STREAMS, CAP        400 symbols, two streams each (depth and trades), at most 160 streams per connection
    plan()                       connections and addresses under the venue's documented limits
    resync_rows(lost)            symbols hit and stale symbol-seconds after `lost` messages vanish on one connection,
                                 per symbol against per connection, at two snapshot depths
    gap_demo()                   Book 3's firm.wsbook on a synthetic depth stream with one lost event: what it reports
    budget()                     one 6,000-weight minute split among three strategies
    skew_series()                a labelled simulation: a venue clock drifting against ours, and its estimate
"""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("cryptofeed", "ratelimit", "wsbook"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
import firm_cryptofeed as cf  # noqa: E402
import firm_ratelimit as frl  # noqa: E402
import firm_wsbook as wb  # noqa: E402

SYMBOLS, STREAMS, CAP = 400, 2, 160
LIMITS = cf.LIMITS["binance-spot"]
SNAPSHOT_WEIGHT = {"5000 levels": 250, "1000 levels": 50}     # networks/20:F2


def plan():
    return cf.plan_shards(SYMBOLS * STREAMS, LIMITS, CAP)


def symbols_hit(lost, per_conn_symbols, seed=0):
    """Distinct symbols among `lost` messages drawn uniformly from one connection's symbols."""
    rng = np.random.default_rng(seed)
    return len(set(rng.integers(0, per_conn_symbols, lost).tolist()))


def resync_rows(lost=(1, 5, 20)):
    per_conn = CAP // STREAMS
    rules = frl.binance_like().rules
    out = []
    for n in lost:
        hit = symbols_hit(n, per_conn)
        for depth, w in SNAPSHOT_WEIGHT.items():
            a = cf.resync_staleness(hit, w, rules)
            b = cf.resync_staleness(per_conn, w, rules)
            out.append({"lost": n, "depth": depth, "hit": hit, "per_symbol_s": a["symbol_seconds"],
                        "per_conn_s": b["symbol_seconds"], "per_conn_done_s": b["done_ms"] / 1000})
    return out


def gap_demo():
    book = wb.Book()
    book.snapshot(100, [(10_000, 5)], [(10_010, 5)])
    events = [(101, 101, [(10_000, 6)], []), (102, 103, [], [(10_010, 4)]), (105, 106, [(9_990, 3)], [])]
    return [book.apply(u0, u1, b, a) for u0, u1, b, a in events]      # the event 104 is lost


def budget():
    return cf.allocate(6000, {"market making": 4000, "arbitrage": 3000, "risk": 500},
                       {"market making": 3, "arbitrage": 2, "risk": 1})


def skew_series(n=36_000, seed=4, window=600):
    """One hour at ten events a second: the venue's clock runs 3 ms ahead of ours at the start and 5 ms at the end;
    one-way delay 0.8 ms plus exponential jitter of mean 0.5 ms (assumptions)."""
    rng = np.random.default_rng(seed)
    t = np.arange(n) * 100.0
    offset = 3.0 + 2.0 * t / t[-1]
    recv = t + 0.8 + rng.exponential(0.5, n)
    event = t + offset
    est = cf.skew(event, recv, window)
    true = [(tt, 0.8 - (3.0 + 2.0 * tt / t[-1])) for tt, _ in est]
    return est, true
