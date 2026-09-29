"""Numbers gate: every numerical answer printed in Book 17, chapter 8 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_owners as o  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


def test_nbim():
    n = o.nbim()
    assert r(n["total_bp"]) == 3.5 and r(n["internal_bp"]) == 2.3 and r(n["external_bp"]) == 27.7
    assert r(n["external_base_bp"]) == 16.5 and r(100 * n["external_share"]) == 5.0
    assert r(n["personnel_per_head_nok_m"], 2) == 3.65 and r(n["personnel_per_head_usd_k"], 0) == 352
    assert r(n["assets_usd_bn"], 0) == 2051 and r(n["assets_per_employee_usd_bn"], 2) == 3.03
    assert r(o.usd_per("NOK"), 5) == 0.09644 and r(100 * (1756 + 1182) / 7537, 0) == 39


def test_cpp():
    c = o.cpp()
    assert r(c["total_bp"]) == 81.8 and r(c["external_bp"]) == 59.7 and r(c["operating_bp"]) == 22.1
    assert r(100 * c["external_bp"] / c["total_bp"], 0) == 73 and r((1976 + 2758) / 1757) == 2.7
    assert r(100 * c["assets_usd_bn"] / o.nbim()["assets_usd_bn"], 1) == 27.7


def test_breakeven():
    b = o.team_breakeven(fees=(10, 20, 25, 40))
    assert [r(b[f] / 1000, 3) for f in (10, 20, 40)] == [5.02, 2.51, 1.255]
    assert r(o.team_breakeven(20, fees=(25,))[25] / 1000, 2) == 3.42
    assert r(5.02 / 2000 * 1e4) == 25.1 and r(15 / 2.51) == 6.0 and 15e3 * 20 / 1e4 == 30
    assert r((50 - 5) / 0.8, 2) == 56.25 and r(0.5 / 2 * math.sqrt(10)) == 0.8
