"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 30 (text and solutions)."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import pl_survpipe as P

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/platforms/30-surveillance-and-compliance-technology"


def _csv(name):
    return list(csv.DictReader(open(FIG / name)))


def test_small_runs():
    d = P.day_population("spoofing", 0)
    assert len(d["score"]) >= 1150
    assert P.report_study()["event-sourced"] == {"reports": 2582, "invalid": 0, "missing": 0, "extra": 0,
                                                  "mismatched": 0, "trades": 2500}


def test_queue_csv():
    q = {r["fpr_pct"]: r for r in _csv("queue.csv")}
    assert [q[k]["alerts_per_day"] for k in ("0.2", "0.5", "1")] == ["4.8", "10.7", "21.2"]
    assert [q[k]["backlog_end"] for k in ("0.2", "0.5", "1")] == ["0", "0", "330"]
    assert [q[k]["planted_raised"] for k in ("0.2", "0.5", "1")] == ["32", "36", "38"]
    assert (q["1"]["reviewed_oldest"], q["1"]["within5_oldest"], q["1"]["reviewed_score"], q["1"]["within5_score"],
            q["1"]["median_wait_oldest"], q["1"]["planted_total"]) == ("28", "11", "37", "37", "7", "45")


def test_comms_and_reports():
    c = _csv("comms.csv")[0]
    assert (c["conversations"], c["traces"], c["invisible"], c["broad_hits"], c["broad_true"], c["narrow_hits"]) == (
        "40", "25", "15", "464", "10", "10")
    r = {x["kind"]: (x["legacy"], x["event_sourced"]) for x in _csv("reports.csv")}
    assert r == {"invalid": ("41", "0"), "missing": ("41", "0"), "extra": ("6", "0"), "mismatched": ("40", "0"),
                 "reports": ("2506", "2582")}
    assert P.queue_study(0.01, "score")["planted_reviewed"] == 37


def test_exercise_7():
    r = P.queue_study(0.01, "oldest", analysts=3)
    assert (r["backlog_end"], r["planted_reviewed"], r["planted_within_5"]) == (0, 38, 38)
