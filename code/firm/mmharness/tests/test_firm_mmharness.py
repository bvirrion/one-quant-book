import pathlib
import sys
from dataclasses import replace

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_mmharness as h  # noqa: E402
import firm_tape as ft  # noqa: E402

CFG = replace(ft.TapeConfig(), seconds=600.0, news_at=None)


def test_decomposition_adds_up_and_matches_pnl():
    r = h.run_tape(h.SymmetricQuoter(100, 300), CFG, fees=h.Fees(-0.002, 0.003))
    assert len(r.fills) > 5
    for ref in ("mid", "truth"):
        d = r.decompose(5.0, ref)
        assert np.isclose(d["total"], d["spread"] + d["adverse"] + d["inventory"] + d["fees"])
        assert np.isclose(d["total"], r.pnl(ref))


def test_position_limit_and_fill_log():
    r = h.run_tape(h.SymmetricQuoter(100, 200), CFG)
    _, inv = r.inventory()
    assert np.abs(inv).max() <= 200 + 100          # one order may be in flight when the limit binds
    assert set(np.unique(r.fills["side"])) <= {-1, 1} and (r.fills["qty"] > 0).all()


def test_no_feedback_on_own_orders():
    """Quoting off the book without one's own orders keeps messages near the market's own rate of change."""
    r = h.run_tape(h.SymmetricQuoter(100, 300), CFG)
    assert r.messages < 0.1 * len(r.tape.msgs)


class _Taker:
    def __init__(self):
        self.done = False

    def on_start(self, ctx):
        pass

    def on_market(self, ctx, t, top):
        if not self.done and t > 10:
            self.done = True
            ctx.take(1, 300)

    def on_fill(self, ctx, fill):
        pass


def test_aggressive_fill_pays_taker_fee():
    r = h.run_tape(_Taker(), CFG, fees=h.Fees(-0.002, 0.003))
    assert r.volume() == 300 and not r.fills["passive"].any()
    assert np.isclose(r.fees_paid, 0.003 * 300)


def test_deterministic():
    a = h.run_tape(h.SymmetricQuoter(100, 300), CFG)
    b = h.run_tape(h.SymmetricQuoter(100, 300), CFG)
    assert np.array_equal(a.fills, b.fills) and a.messages == b.messages


class _Watcher(h.SymmetricQuoter):
    wants_queue_position = True

    def __init__(self):
        super().__init__(100, 300)
        self.seen = {}

    def on_market(self, ctx, t, top):
        super().on_market(ctx, t, top)
        for cid in ctx.working():
            a = ctx.ahead(cid)
            if a is not None:
                self.seen.setdefault(cid, []).append(a)


def test_queue_position_only_moves_forward():
    w = _Watcher()
    h.run_tape(w, CFG)
    assert len(w.seen) > 5
    for xs in w.seen.values():
        assert min(xs) >= 0 and all(b <= a for a, b in zip(xs, xs[1:], strict=False))


def test_feed_messages_and_counterparty_log():
    seen = []

    class Q(h.SymmetricQuoter):
        def on_market(self, ctx, t, top):
            seen.append(ctx.last["kind"])
            super().on_market(ctx, t, top)

    r = h.run_tape(Q(100, 300), CFG)
    assert {b"A", b"X", b"E"} <= set(seen)
    assert len(r.extra["informed"]) == len(r.fills) and r.extra["informed"].any() and not r.extra["informed"].all()
