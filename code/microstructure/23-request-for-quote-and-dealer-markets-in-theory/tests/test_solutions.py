"""Numbers gate: every numerical answer printed in Book 10, chapter 23 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_otc import chase_study, common_study, dgp_study, network_study, rfq_study  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


def test_search_model():
    d = dgp_study()
    assert [r(d[k]["spread_share"] * 1e4) for k in (10.0, 100.0, 1000.0)] == [210.0, 36.7, 4.0]
    assert r(d[100.0]["mu"][2], 4) == 0.0016 and r(0.2 * 0.8 / 102.2, 4) == 0.0016


def test_rfq_named_result():
    s = rfq_study()
    assert [(s[k]["best_n"], r(s[k]["cost"], 2)) for k in (0.1, 0.25, 0.5, 1.0, 2.0, 3.0)] == [
        (16, 5.52), (7, 6.92), (4, 8.02), (2, 9.09), (1, 10.0), (1, 10.0)]
    assert abs(s["check"][0] - s["check"][1]) < 0.001
    assert (r(s[1.0]["curve"][0], 2), r(s[1.0]["curve"][1], 2)) == (10.0, 9.09)
    assert r(s[0.5]["curve"][11] - s[0.5]["cost"], 1) == 2.0
    c = common_study()
    assert [c[k]["best_n"] for k in (0.0, 2.0, 5.0)] == [6, 4, 3]
    assert r((math.sqrt(29) - 2) * 0.5641896, 2) == 1.91


def test_chasing_network_and_exercise():
    c = chase_study()
    assert [c[v]["informed"] for v in (0.0, 1.5, 3.0)] == [3.5, 2.0, 0.5] and c[0.0]["uninformed"] == 2.0
    n = network_study()
    assert (r(n["core"]["hops"], 2), r(n["periphery"]["hops"], 2), r(n["core"]["markup"]), r(n["periphery"]["markup"])) == (
        1.77, 2.58, 9.2, 10.4)
    from firm_otcsearch import best_n, rfq_cost
    k = best_n(10.0, 5.0, 0.0, 1.0)
    assert (k, r(rfq_cost(k, 10.0, 5.0, 0.0, 1.0), 2)) == (3, 7.77)
