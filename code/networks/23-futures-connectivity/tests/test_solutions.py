"""Numbers gate: every number printed in Book 14, chapter 23 (text and solutions)."""
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_futures as n  # noqa: E402

gm = n.gm


def test_fees_and_plans():
    assert (n.FULL.max_tps, n.ULTRA.max_tps, n.FULL.fee_first, n.FULL.fee_after, n.ULTRA.fee_first) == (150, 250, 260, 520, 780)
    assert gm.session_cost(n.FULL, 10) == 3640 and 10 * 150 == 1500
    assert gm.plan_sessions(3000, (n.FULL, n.ULTRA)) == (8320, {"HF Full": 5, "HF Ultra": 9})
    assert gm.session_cost(n.FULL, 20) == 8840 and 8840 - 8320 == 520
    assert gm.both_lost(1e-5, 1e-5) == pytest.approx(1e-10) and round(1 / gm.both_lost(1e-5, 1e-5, 0.5), -3) == 200000
    assert gm.session_cost(n.FULL, 12) - 260 == 5 * 260 + 6 * 520 == 4420


@pytest.mark.reference
def test_race_curves():
    c = n.curves()
    p = [x[0] for x in c["solo"]]
    assert (round(100 * p[0], 1), round(100 * p[-1], 1)) == (10.0, 59.7)
    assert (round(100 * (p[1] - p[0]), 1), round(100 * (p[-1] - p[-2]), 1)) == (8.4, 1.8)
    assert round(100 * c["everyone"][-1][0], 1) == 10.2
    assert (round(c["everyone"][0][2], 1), round(c["everyone"][-1][2], 1)) == (25.4, 35.8)
    assert {round(100 * x[0], 1) for x in c["segment"]} == {9.8}
    m = dict(n.marginal(c["solo"]))
    assert (round(m[2], 1), round(m[12], 1)) == (840.0, 180.5)
    total = (p[-1] - p[0]) * n.RACES * n.VALUE_EUR
    assert (round(total), round(total / 11)) == (4973, 452)
    assert n.last_paying(c["solo"]) == 6 and all(m[k] < 520 for k in range(7, 13))


def test_small_runs():
    p1, _, _ = gm.win_rate(n.PARALLEL, 1, others=4, n=500)
    p6, _, _ = gm.win_rate(n.PARALLEL, 6, others=4, n=500)
    s6, _, _ = gm.win_rate(n.SEGMENT, 6, others=4, n=5000)
    assert p6 > p1 and abs(s6 - 0.2) < 0.03
    assert n.fee(6) == 260 and n.fee(7) == 520
