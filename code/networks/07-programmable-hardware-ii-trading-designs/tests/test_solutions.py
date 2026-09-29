"""Numbers gate: every number printed in Book 14, chapter 7 (text and solutions)."""
import functools
import pathlib
import sys

import numpy as np
import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_hwtrade as h  # noqa: E402


@functools.lru_cache
def paths():
    return h.paths()


def test_table_and_controls():
    rows = {(1_000_200, 10_000, -1): (108, 5), (1_000_300, 10_000, -1): (133, 27), (1_000_300, 600, -1): (131, 29),
            (1_000_300, 10_000, 3000): (41, 119)}
    for (t, m, k), (n, r) in rows.items():
        o, rej = h.run(t, m, k)
        assert (len(o), rej) == (n, r)
    assert (133 - 108, 27 - 5, 160 - 113) == (25, 22, 47)
    assert len(h.hw.triggers(h.fixture()[0], 1_000_200)) == 113 and len(h.hw.triggers(h.fixture()[0], 1_000_300)) == 160
    assert len(h.fixture()[0]) == 992


def test_cycles_and_bucket():
    d = h.decision_cycles()
    assert set(d[:, 0]) == {10} and set(d[:, 1]) == {0}                   # ten cycles from the first beat
    assert 57 // 8 == 7 and 10 * 6.4 == pytest.approx(64) and 2 * 6.4 == pytest.approx(12.8)
    assert h.burst_before_kill(20) == 52 and h.burst_before_kill(100) == 248 and h.burst_before_kill(50) == 126
    assert h.burst_before_kill(16 / 156.25) == 4 and round(156.25e6 / 64 / 1e6, 2) == 2.44
    o, _ = h.hw.CycleModel(burst=1, refill=10_000).run(h.fixture()[1], 1_000_300, 10_000)
    assert len(o) == 1
    base, _ = h.run(1_000_300)
    assert len(h.run(1_000_300, 10_000, base[9][0] - 1)[0]) == 9


def test_paths_and_race():
    p = paths()
    hard = [s.p50_ns for s in p["hardware_stages"]]
    assert round(sum(hard), 1) == 816.5 and round(sum(hard) / 1000, 2) == 0.82 and round(19.2 / 816.5, 2) == 0.02
    assert np.ptp(p["hardware"]) == 0
    q = np.quantile(p["software"], [0.5, 0.99])
    assert round(q[0] / 1000, 2) == 4.39 and round(q[1] / 1000, 1) == 35.3
    assert round((q[0] - 816.5) / 1000, 2) == 3.57 and round((q[1] - 816.5) / 1000, 1) == 34.5
    assert round(h.win_probability(p["hardware"], 1000), 2) == 0.75 and round(h.win_probability(p["software"], 1000), 4) == 0.0001
    assert h.win_probability(p["hardware"], 5000) == 1.0 and round(h.win_probability(p["software"], 5000), 2) == 0.57
    assert 263 + 120 + 19.2 + 120 + 295 == pytest.approx(817.2)


def test_small_runs():
    """At reduced size: a faster competitor lowers the win probability; the hardware path is constant."""
    p = h.paths(n=5000)
    assert h.win_probability(p["hardware"], 700) < h.win_probability(p["hardware"], 1500)
    assert np.ptp(p["hardware"]) == 0 and np.median(p["software"]) > np.median(p["hardware"])
