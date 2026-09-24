import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from feed_demo import TRADES, clean, inversions, receive_times, replay, vwap


def test_replay_gives_a_never_crossed_level_one():
    book, l1 = replay()
    assert len(l1) == 2020 and not book.errors
    assert all(bb < ba for _, bb, _, ba, _ in l1 if bb is not None and ba is not None)


def test_jitter_reorders_messages_and_constant_latency_does_not():
    ex = np.array([x[0] for x in replay()[1]], dtype=float)
    assert inversions(ex, ex + 200_000.0) == 0
    assert inversions(ex, receive_times(ex, 200_000.0, 1_000_000.0, 1)) > 0


def test_cleaning_the_tape():
    kept, dropped = clean(TRADES)
    assert sorted(r[0] for r in dropped) == [6, 9] and abs(vwap(kept) - vwap(TRADES)) > 0.5
