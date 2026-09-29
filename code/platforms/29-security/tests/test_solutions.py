"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 29 (text and solutions)."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import pl_accessctl as P

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/platforms/29-security"


def _csv(name):
    return list(csv.DictReader(open(FIG / name)))


def test_small_runs():
    t = P.toxic_summary()
    assert (len(t["before"]["roles"]), len(t["before"]["users"]), len(t["after"]["users"])) == (5, 60, 0)
    assert [ok for _, ok, _ in P.stolen_key_attempts()] == [True, False, False, True, False, False]
    assert P.exposure_days(90) == 45 and P.exposure_days(7) == 3.5


def test_detection_csv():
    d = {r["extra_pct"]: r for r in _csv("detection.csv")}
    assert (d["30"]["cusum_lagged_found"], d["30"]["cusum_lagged_median"]) == ("19", "22.0")
    assert (d["20"]["cusum_lagged_found"], d["20"]["cusum_lagged_median"]) == ("12", "34.5")
    assert (d["50"]["cusum_lagged_found"], d["50"]["cusum_lagged_median"]) == ("20", "12.0")
    assert (d["30"]["day_trailing_found"], d["30"]["cusum_trailing_found"], d["30"]["day_lagged_found"]) == ("1", "5", "8")
    assert (d["100"]["cusum_trailing_found"], d["100"]["cusum_trailing_median"]) == ("20", "5.0")
    h = {r["detector"]: r["threshold"] for r in _csv("thresholds.csv")}
    assert h == {"day_trailing": "4.851", "cusum_trailing": "11.158", "day_lagged": "4.252", "cusum_lagged": "12.709"}


def test_full_delays():
    r = P.delays(0.3)
    assert r["CUSUM, lagged"] == (19, 22.0) and r["single day, trailing"][0] == 1


def test_exercise_7():
    r = P.delays(0.3, k=0.25)
    assert r["CUSUM, lagged"] == (20, 20.5)
