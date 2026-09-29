import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_regmap as rm  # noqa: E402

ROWS = [{"jurisdiction": "A", "activity": "x", "status": "required", "regime": "R1", "category": "c", "reference": "r",
         "decision_days": 30, "as_of": "2026-01", "source": "s"},
        {"jurisdiction": "A", "activity": "y", "status": "check", "regime": "R1", "category": "c", "reference": "r",
         "decision_days": None, "as_of": "2024-01", "source": "s"},
        {"jurisdiction": "B", "activity": "x", "status": "required", "regime": "R2", "category": "c", "reference": "r",
         "decision_days": 90, "as_of": "2026-06", "source": "s"}]


def test_query_regimes_longest():
    q = rm.query(ROWS, {("A", "x"), ("A", "y")})
    assert len(q) == 2 and rm.regimes(q) == [("A", "R1")] and rm.longest_decision(q) == (30, "A", "R1")
    assert rm.longest_decision(ROWS) == (90, "B", "R2") and rm.longest_decision(ROWS[1:2]) is None


def test_check_and_stale():
    assert rm.check(ROWS) == []
    assert [r["as_of"] for r in rm.stale(ROWS, "2026-09", 12)] == ["2024-01"]
