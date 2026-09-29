"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 27 (text and solutions)."""
import csv
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import pl_goldtest as P

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/platforms/27-testing-and-continuous-delivery"


def _csv(name):
    return list(csv.DictReader(open(FIG / name)))


def test_small_runs():
    port = dict(list(P.portfolio().items())[::6])              # ten instruments, every product
    ex = P.experiment(port, seeds=2)
    r = P.rates(ex, 3.0)
    assert r["put sign"][0] == r["put sign"][1] and P.rates(ex, 3.0, pinned=True)["noise_run"] == 1.0
    assert abs(P.noise_theory(2.0) - 0.1573) < 1e-4


def test_tolerance_csv():
    rows = {r["k"]: r for r in _csv("tolerance.csv")}
    assert [rows[k]["asian_fix"] for k in ("1", "2", "3", "4", "5", "6")] == ["1.00", "1.00", "0.90", "0.55", "0.45", "0.35"]
    assert [rows[k]["noise_run"] for k in ("2", "3", "4", "5", "6")] == ["1.000", "0.600", "0.200", "0.025", "0.000"]
    assert [rows[k]["cost"] for k in ("2", "3", "5")] == ["980", "1588", "5525"]
    assert (rows["2"]["day_count_all"], rows["2"]["day_count_asian"], rows["1"]["finer_grid"]) == ("40/60", "0.00", "0/10")
    assert _csv("pinned.csv")[0] == {"asian_fix": "20/20", "day_count_asian": "20/20", "day_count_all": "60/60",
                                     "noise_run": "1.000"}


def test_trains_servers_stages():
    t = {r["cadence_days"]: r for r in _csv("trains.csv")}
    assert (t["7"]["changes"], t["7"]["mean_lead_days"], t["7"]["mean_batch"], t["7"]["bisect_steps"]) == (
        "533", "3.46", "10.25", "3.93")
    assert P.eight_servers()["refused"] == ["router8"]
    s = {r["stage"]: float(r["seconds"]) for r in _csv("measured_stages.csv")}
    assert s["unit"] < s["golden"] < s["end to end"]
    assert (s["unit"], s["golden"], s["end to end"]) == (0.02, 0.33, 1.62)


@pytest.mark.reference
def test_full_experiment():
    ex = P.experiment()
    r = P.rates(ex, 5.0)
    assert (r["Asian fixing"], round(r["noise_run"], 3)) == ((9, 20), 0.025)


@pytest.mark.reference
def test_doubled_paths():
    r = P.doubled_paths(5.0)
    assert (r["Asian fixing"], round(r["noise_run"], 3)) == ((14, 20), 0.4)
