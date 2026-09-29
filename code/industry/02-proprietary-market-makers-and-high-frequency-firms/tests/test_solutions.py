"""Numbers gate: every numerical answer printed in Book 17, chapter 2 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_profiles as p  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


def test_facts_are_admissible():
    assert p.check() == []
    assert len(p.facts()) == 24


def test_gap_named_result():
    g = p.gap()
    assert g["listed"] == [4] and g["private_median"] == 2 and g["revenue_private"] == 0
    assert p.coverage() == {"Virtu Financial": 4, "Jane Street": 4, "Hudson River Trading": 3, "Tower Research": 2,
                            "DRW": 3, "Jump Trading": 2, "XTX Markets": 2, "Citadel Securities": 0}


def test_cme():
    s = p.cme_shares()
    assert r(100 * s["globex"], 0) == 93 and r(100 * s["open_outcry"]) == 3.3
    c = p.cme()
    assert r(100 * (c[1]["open_outcry"] / c[0]["open_outcry"] - 1)) == -10.1
    assert [r(x["globex"] / 1000) for x in c] == [24.5, 26.2]


def test_subsidiary_and_broker_dealer():
    j = p.jse()
    assert r(100 * j["rev_change"]) == -35.4 and r(100 * j["eq_change"]) == 15.1
    assert (r(100 * j["margin"][1]), r(100 * j["margin"][0])) == (65.8, 68.0) and r(100 * j["roe"]) == 15.3
    c = p.citadel_2023()
    assert c["capital"] == 4693 and r(c["leverage"]) == 11.2


def test_virtu_and_races():
    assert r(3632.1 / 1027, 2) == 3.54
    assert round(0.82 + 0.85 - 1, 2) == 0.67
