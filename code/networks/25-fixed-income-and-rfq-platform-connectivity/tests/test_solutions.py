"""Numbers gate: every number printed in Book 14, chapter 25 (text and solutions)."""
import math
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_rfq as n  # noqa: E402

rl = n.rl


def test_timer():
    assert round(100 * rl.miss_prob(n.OURS, n.TIMER_MS), 2) == 1.94
    auto = rl.Pipeline(n.OURS.stages)
    assert rl.miss_prob(auto, 2000) == 0.0 and round(100 * rl.miss_prob(n.OURS, 100), 1) == 4.3
    m = n.miss_curves()
    assert round(100 * m["auto"][0], 1) == 2.4 and round(100 * m["auto"][3], 3) == 0.002 and m["auto"][4] == 0.0
    p_person = 0.5 * math.erfc(math.log(2000 / 6000) / 0.5 / math.sqrt(2))
    assert round(100 * p_person, 1) == 98.6 and round(2 * p_person, 2) == 1.97


@pytest.mark.reference
def test_rules_and_values():
    r = n.rules_at()
    assert [round(100 * r[k]["win"], 1) for k in n.RULES] == [19.2, 26.4, 39.0]
    assert [round(100 * r[k]["lost_to_speed"], 1) for k in n.RULES] == [0.0, 1.6, 5.7]
    v = n.values()
    assert [round(100 * v[k]["faster"], 1) for k in n.RULES] == [0.0, 2.3, 12.6]
    assert [round(100 * v[k]["cheaper"], 1) for k in n.RULES] == [0.9, 1.0, 0.9]
    assert round(v["first_ok"]["faster"] / v["first_ok"]["cheaper"]) == 15
    x = rl.auction(5, n.with_pricing(50.0), n.THEIRS, "first_ok")["win"]
    assert round(100 * x, 1) == 19.0 and x < r["expiry"]["win"]


def test_small_runs():
    a = rl.auction(5, n.OURS, n.THEIRS, "first_ok", n=2000)
    b = rl.auction(5, n.with_pricing(200.0), n.THEIRS, "first_ok", n=2000)
    assert a["win"] > b["win"] and n.OURS.stages[2].median_ms == 20.0
