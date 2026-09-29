"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 17 (text and solutions)."""
import csv
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import pl_posservice as P

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/platforms/17-position-and-pnl-services"


def _csv(name):
    return list(csv.DictReader(open(FIG / name)))


def test_small_runs():
    r = P.at_close(seeds=(2,), seconds=900.0)[0]
    assert r["merged+bust_pos_err"] == 0 and r["fills"] > 0


@pytest.mark.reference
def test_full_days_reproduce_the_table():
    rows = P.at_close()
    got = [(r["seed"], r["lost"], r["session_pos_err"], r["merged_pos_err"]) for r in rows]
    want = [(int(r["seed"]), int(r["lost"]), int(r["session_pos_err"]), int(r["merged_pos_err"])) for r in _csv("at_close.csv")]
    assert got == want


def test_named_result_numbers():
    s = {r["service"]: r for r in _csv("summary.csv")}
    assert [(int(s[k]["mean_abs_pos"]), float(s[k]["mean_abs_pnl"])) for k in
            ("session only", "with drop copy", "with drop copy and bust")] == [(290, 52.4), (220, 28.4), (0, 0.0)]
    rows = _csv("at_close.csv")
    assert [int(r["lost"]) for r in rows] == [0, 1, 4, 0, 3, 0, 0, 0, 1, 0]
    assert [float(r["pending_s"]) for r in rows if int(r["lost"])] == [60.5, 62.1, 63.3, 60.5]
    r3 = rows[2]
    assert (float(r3["drop_min"]), int(r3["true_pos"]), int(r3["session_pos_err"]), float(r3["session_pnl_err"])) \
        == (33.0, -3300, 600, 252.0)
    assert max(abs(int(r["session_pos_err"])) for r in rows) == 600
    t = _csv("timeline.csv")
    last = t[-1]
    assert (int(last["session"]), int(last["merged"]), int(last["merged_bust"]), int(last["truth"])) == (-2700, -3200, -3300,
                                                                                                        -3300)


@pytest.mark.reference
def test_exercise_7_cancel_on_disconnect():
    rows = P.at_close(cod=True)
    assert [r["lost"] for r in rows] == [0] * 10
    assert all(r["session_pos_err"] == r["merged_pos_err"] for r in rows)
    assert round(sum(abs(r["session_pos_err"]) for r in rows) / 10) == 220
