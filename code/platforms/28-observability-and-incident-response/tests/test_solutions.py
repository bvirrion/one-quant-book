"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 28 (text and solutions)."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import pl_observe as P

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/platforms/28-observability-and-incident-response"


def _csv(name):
    return list(csv.DictReader(open(FIG / name)))


def test_small_runs():
    rows = {r["rule"]: r for r in P.compare(days=3)}
    assert rows["process heartbeat"]["feed stall"] is None
    assert rows["age above 5 s"]["feed stall"] == 5.0 and rows["burn rate (1 h and 6 h)"]["feed stall"] == 56.0
    assert P.clock(P.at(12, 3)) == "12:03:00"


def test_rules_and_budget():
    got = [(r["rule"], r["feed_stall_s"], r["intermittent_s"], r["slow_consumer_s"], r["false_pages_month"])
           for r in _csv("rules.csv")]
    assert got == [("process heartbeat", "none", "none", "none", "0"), ("age above 5 s", "5", "5", "100", "18"),
                   ("age above 30 s", "30", "none", "600", "1"), ("age above 60 s", "60", "none", "1200", "0"),
                   ("burn rate (1 h and 6 h)", "56", "191", "151", "1")]
    assert _csv("budget.csv")[0] == {"bad_seconds": "115", "budget_seconds": "702", "used_pct": "16.4",
                                     "pauses_over_5s": "18"}
    assert [r["clock"] for r in _csv("timeline.csv")] == ["12:03:00", "12:03:05", "12:03:30", "12:03:56", "12:04:00",
                                                          "12:24:00", "12:24:00"]


def test_trace():
    spans = P.traced(0.0, 60.0)
    assert [s.name for s in spans][-2:] == ["risk: queue", "risk: compute"]
    assert abs((spans[0].end - spans[0].start) - 60.00132) < 1e-9


def test_exercise_7():
    f = P.false_pages(1.6)
    assert (f["age above 5 s"], f["age above 30 s"], f["burn rate (1 h and 6 h)"]) == (36.0, 3.0, 1.0)
