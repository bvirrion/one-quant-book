"""Numbers gate: every numerical answer printed in Book 16, chapter 17 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_regmap as m  # noqa: E402

rm = m.rm


def test_map_is_sound():
    r = m.rows()
    assert len(r) == 20 and rm.check(r) == [] and len(rm.regimes(r)) == 10
    assert sorted({x["jurisdiction"] for x in r}) == ["EU", "HK", "UK", "US"]
    assert len(rm.stale(r, "2027-12", 12)) == 20 and rm.stale(r, "2027-09", 12) == []


def test_profiles():
    p = m.profiles()
    assert [len(v["rows"]) for v in p.values()] == [2, 5, 6] and [len(v["regimes"]) for v in p.values()] == [1, 4, 5]
    assert [v["longest"][:2] for v in p.values()] == [(183, "UK")] * 3
    assert p["London, Chicago and Hong Kong"]["by_status"] == {"required": 2, "obligation": 1, "check": 3}
    q = rm.query(m.rows(), m.EU_MM)
    assert len(q) == 3 and len(rm.regimes(q)) == 2 and rm.longest_decision(q)[:2] == (183, "EU")
    assert dict(m.PERIODS)["US: with the 90-day extension"] == 120 + 90 and len(rm.ALGO_CHECKLIST) == 5


def test_small_runs():
    bad = [{"jurisdiction": "X", "activity": "a", "status": "maybe", "regime": "r", "category": "c", "reference": "",
            "decision_days": None, "as_of": "2026", "source": "s"}]
    assert [p[1] for p in rm.check(bad)] == ["empty reference", "bad status maybe", "as_of not YYYY-MM"]
