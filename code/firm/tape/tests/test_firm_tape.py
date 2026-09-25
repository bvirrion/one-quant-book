"""Acceptance tests of firm.tape: determinism, a consistent feed, and the properties later chapters use."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_tape import Book, TapeConfig, simulate, simulate_pair

CFG = TapeConfig(seconds=1800.0, news_at=900.0, seed=5)
TAPE = simulate(CFG)


def test_deterministic():
    again = simulate(CFG)
    assert np.array_equal(TAPE.msgs, again.msgs) and np.array_equal(TAPE.trades, again.trades)


def test_feed_rebuilds_the_top_of_book_and_never_crosses():
    book, n0 = Book(), TAPE.n_open
    for i, m in enumerate(TAPE.msgs):
        book.apply(m)
        if i >= n0 - 1:
            r = TAPE.top[i]
            assert book.best() == (r["bid"], r["bid_qty"], r["ask"], r["ask_qty"])
    assert (TAPE.top["ask"] > TAPE.top["bid"]).all()
    assert not book.orders or all(q > 0 for _, _, q in book.orders.values())


def test_trades_match_executions_and_prices_are_at_the_touch():
    e = TAPE.msgs[TAPE.msgs["kind"] == b"E"]
    assert len(e) == len(TAPE.trades) and (e["agg"] == -e["side"]).all()
    assert np.array_equal(e["price"], TAPE.trades["price"])


def test_mid_tracks_the_efficient_price():
    mid = TAPE.mid()[TAPE.n_open:]
    vi = np.searchsorted(TAPE.v_t, TAPE.top["t"][TAPE.n_open:], side="right") - 1
    assert np.abs(TAPE.v[vi] - mid).mean() < 2.0


def _imbalance_and_markouts(tape):
    top = tape.top[tape.n_open:]
    mid = 0.5 * (top["bid"] + top["ask"])
    imb = (top["bid_qty"] - top["ask_qty"]) / (top["bid_qty"] + top["ask_qty"])
    ch = np.flatnonzero(np.diff(mid) != 0)
    pos = np.searchsorted(ch, np.arange(len(mid)))
    ok = pos < len(ch)
    nxt = np.zeros(len(mid))
    nxt[ok] = np.sign(np.diff(mid))[ch[pos[ok]]]
    tr = tape.trades
    later = np.searchsorted(top["t"], tr["t"] + 10.0, side="right") - 1
    passive = (mid[np.minimum(later, len(mid) - 1)] - tr["price"]) * (-tr["sign"])
    return nxt[ok & (imb > 0.5)] > 0, nxt[ok & (imb < -0.5)] > 0, passive[tr["informed"]], passive[~tr["informed"]]


def test_imbalance_predicts_and_informed_flow_is_toxic():
    """Pooled over six seeds (a statistical property is never asserted on one path)."""
    parts = [_imbalance_and_markouts(simulate(TapeConfig(seconds=900.0, news_at=None, seed=s))) for s in range(6)]
    up_hi, up_lo, inf, non = (np.concatenate([p[i] for p in parts]) for i in range(4))
    assert up_hi.mean() > 0.55 > 0.45 > up_lo.mean()
    assert inf.mean() < 0 < non.mean()


def test_signs_are_autocorrelated():
    s = TAPE.trades["sign"].astype(float)
    assert np.corrcoef(s[:-1], s[1:])[0, 1] > 0.15


def test_pair_shares_the_efficient_price_with_a_delay():
    a, b = simulate_pair(TapeConfig(seconds=300.0, news_at=None, seed=2), latency=0.2)
    assert np.allclose(a.v, b.v) and np.allclose(b.v_t[1:], np.minimum(a.v_t[1:] + 0.2, 300.0))
