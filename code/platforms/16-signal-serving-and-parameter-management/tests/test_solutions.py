"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 16 (text and solutions)."""
import csv
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import pl_paramstore as P

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/platforms/16-signal-serving-and-parameter-management"


def _csv(name):
    return list(csv.DictReader(open(FIG / name)))


def test_small_runs():
    base = P.run(2, P.lots(0.005), 1200.0)
    wrong = P.run(2, P.lots(0.5), 1200.0)
    assert abs(base["pos"]).max() <= P.CAP_SHARES < abs(wrong["pos"]).max()
    assert P.detection(base, wrong, P.T0) is not None


def test_governance(tmp_path):
    g = P.governance(tmp_path)
    assert g["no_unit"] == ["unit '' not accepted for inventory_limit (accepted: bp, percent, fraction)"]
    assert g["percent"] == ["0.5 fraction outside [0, 0.02]", "step 0.495 fraction above the allowed 0.005"]
    assert (g["raise_needed"], g["after_one"], g["raise_status"], g["raise_approvals"]) == (2, "pending", "applied",
                                                                                          ["ben", "cleo"])
    assert (round(g["live_as_known_day8"], 4), round(g["live_as_known_now"], 4)) == (0.0075, 0.006)
    assert g["flag_q01"] and not g["flag_q02"] and g["drift"] == [("q02", "inventory_limit", 0.005, 0.5)]
    assert g["audit_ok"] and (P.lots(0.005), P.lots(0.5)) == (2, 200)
    assert P.signals() == [(30.0, 0.8, "v3", "fresh"), (200.0, 0.7, "v3", "fresh"), (600.0, 0.0, "v3", "stale-fallback"),
                           (0.0, 0.0, None, "missing-fallback")]


@pytest.mark.reference
def test_incident_reproduces_the_figures():
    r = P.incident()
    s = {row["policy"]: row for row in _csv("summary.csv")}
    assert round(r["all"]["peak"] / 1e3, 1) == float(s["all at once"]["peak_k"])
    assert round(r["staged"]["dollar_min"] / 1e3, 1) == float(s["staged rollout"]["dollar_min_k"])


def test_named_result_numbers():
    s = {row["policy"]: row for row in _csv("summary.csv")}
    assert [float(s[p]["detect_min"]) for p in ("all at once", "staged rollout", "schema check")] == [5.0, 15.0, 0.0]
    assert [float(s[p]["peak_k"]) for p in ("all at once", "staged rollout", "schema check")] == [410.0, 30.0, 0.0]
    assert [float(s[p]["dollar_min_k"]) for p in ("all at once", "staged rollout")] == [1348.3, 53.3]
    assert round(1348.3 / 53.3) == 25
    d = {row["strategy"]: row["detect_min"] for row in _csv("detection.csv")}
    assert [d[f"q{i:02d}"] for i in range(1, 11)] == ["15", "5", "5", "15", "15", "5", "30", "5", "5", "50"]


@pytest.mark.reference
def test_exercise_7_quiet_canary():
    r = P.incident(seeds=(10, 1, 2, 3, 4, 5, 6, 7, 8, 9))
    s = r["staged"]
    assert (s["detect_min"], round(s["peak"] / 1e3), round(s["dollar_min"] / 1e3)) == (35.0, 1310, 5443)
