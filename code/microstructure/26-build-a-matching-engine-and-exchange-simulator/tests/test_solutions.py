"""Numbers gate: every numerical answer printed in Book 10, chapter 26 (text and solutions). Timings are checked as
orders of magnitude (they are measured, and the text says so)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_exchsim import determinism, recovery, scenario, throughput  # noqa: E402


def test_scenario_reports():
    r = [(t, k, cl, q, why) for t, k, cl, q, why in scenario() if k != "S"]
    assert r == [(1.0, "A", 1, 300, ""), (2.0, "A", 2, 100, ""), (2.0, "E", 1, 100, ""), (2.0, "E", 2, 100, ""),
                 (3.0, "A", 3, 500, ""), (3.0, "E", 1, 200, ""), (3.0, "E", 3, 200, ""), (3.0, "C", 3, 300, "I"),
                 (4.0, "A", 4, 200, ""), (5.0, "A", 5, 100, ""), (5.0, "E", 4, 100, ""), (5.0, "E", 5, 100, ""),
                 (6.0, "J", 6, 0, "X"), (7.0, "J", 5, 0, "L"), (10.0, "C", 4, 100, "E")]


def test_recovery():
    r = recovery()
    assert (r["messages"], r["lost_a"], r["lost_b"], r["after_arbitration"], r["retransmit_requests"]) == (
        5793, 308, 517, 30, 30)
    assert r["complete"] and r["snapshot_ok"] and r["snapshots"] == 20
    assert (round(100 * 308 / 5793, 1), round(100 * 517 / 5793, 1), round(100 * 30 / 5793, 2)) == (5.3, 8.9, 0.52)
    q = recovery(600.0, False)
    assert (q["lost_a"], q["lost_b"], q["retransmit_requests"]) == (0, 166, 0)
    assert 5001 + 12 == 5013


def test_determinism_and_speed():
    d = determinism()
    assert d["same"] and d["sha"] == "f7ede7cfa7b3" and d["fixture_ok"] and d["records"] == 17059
    t = throughput()
    assert 20_000 < t["python"] < 200_000 and t["cpp"] > 200_000
    assert t["cpp_out"] == ["codec: 4866 golden messages round-trip",
                            "engine: 17059 journal records, 3518 executions, output byte-identical to Python (1677645 bytes)"]
