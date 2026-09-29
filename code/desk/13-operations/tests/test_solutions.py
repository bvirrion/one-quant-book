"""Numbers gate: every numerical answer printed in Book 16, chapter 13 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_ops as m  # noqa: E402

om = m.om


def r(x, d=2):
    return round(float(x), d)


def test_inputs_and_hand_numbers():
    assert (m.LAM, m.MU, r(m.LAM / m.MU)) == (15.0, 1.5, 10.0)
    assert r(100 * math.exp(-m.MU * 2.5)) == 2.35 and r(100 * math.exp(-m.MU * 10), 4) == 0.0
    assert r(om.fail_cost(1, m.VALUE, m.PENALTY_BP, m.FAIL_DAYS, m.INTERNAL)) == 2500.0
    assert r(om.fail_cost(1, m.VALUE, m.PENALTY_BP, m.FAIL_DAYS)) == 1000.0
    assert r(om.erlang_c(15, 1.5, 11), 3) == 0.682 and r(om.erlang_c(15, 1.5, 12), 3) == 0.449
    assert r(om.erlang_c(15, 1.5, 14), 3) == 0.174


def test_staffing():
    assert (m.staff95("T+2"), m.staff95("T+1"), m.cheapest("T+1")) == (11, 12, 13)
    t = m.table("T+1")
    assert [r(100 * t[c]["late"]) for c in (11, 12, 13, 14, 16)] == [8.37, 3.38, 2.69, 2.49, 2.38]
    assert [round(t[c]["fails"]) for c in (11, 12, 13)] == [1255, 508, 403]
    assert [r(t[c]["fail_cost"]) for c in (11, 12, 13, 16)] == [3.14, 1.27, 1.01, 0.89]
    assert [r(t[c]["total"]) for c in (11, 12, 13, 14)] == [4.46, 2.71, 2.57, 2.61]
    assert r(t[11]["fail_cost"] - t[13]["fail_cost"]) == 2.13
    t2 = m.table("T+2")
    assert r(t2[11]["total"]) == 1.32 and t2[11]["late"] < 1e-5


def test_scenarios_and_ageing():
    s = m.scenarios()
    assert [s[k]["team"] for k in s] == [11, 13, 7, 10] and [s[k]["staff95"] for k in s] == [11, 12, 7, 9]
    assert [r(s[k]["total"]) for k in s] == [1.32, 2.57, 1.42, 1.50]
    assert [r(s[k]["fail_cost"]) for k in s] == [0.0, 1.01, 0.58, 0.30]
    assert [r(100 * x, 1) for x in m.ageing(11)] == [28.6, 26.3, 30.0, 13.9, 1.3]
    assert [r(100 * x, 1) for x in m.ageing(14)] == [50.3, 26.1, 18.3, 5.0, 0.3]


def test_collateral_and_report():
    ours, theirs, disp = m.collateral()
    assert (r(ours), theirs, disp) == (0.7, 0.0, True) and r(100 * (25.3 - 24.4) / 25.3, 1) == 3.6
    assert [s for _, _, s in m.daily_report()] == ["amber", "amber", "amber", "green"]


def test_small_runs():
    assert m.year(12, "T+1")["late"] > m.year(12, "T+2")["late"]


def test_text_extras():
    assert r(om.erlang_c(15, 1.5, 13), 3) == 0.285 and r(100 * math.exp(-5), 2) == 0.67
    assert r(math.exp(-15) * 1e7, 1) == 3.1 and r(100 * m.year(11, "T+2")["late"], 4) == 0.0003
    assert m.VALUE * m.PENALTY_BP * 1e-4 == 500.0
