"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 11 (text and solutions)."""
import csv
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import pl_btengine as P

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/platforms/11-backtest-engine-architecture"


def _csv(name):
    return list(csv.DictReader(open(FIG / name)))


def test_small_runs(tmp_path):
    rows = P.ladder(seeds=(1, 2), seconds=120.0, root=tmp_path)
    assert len(rows) == 2 and all(r["fills3"] > 0 and r["fills4"] > 0 for r in rows)
    s = P.summary(rows)
    assert set(s) >= {"pnl2", "pnl3", "pnl4", "gap", "share_only4"}
    assert len(P.B.ResultsStore(tmp_path / "runs").query(level=4)) == 2
    assert P.rerun_is_identical(tmp_path, seconds=60.0)


@pytest.mark.reference
def test_full_ladder_reproduces_the_figures(tmp_path):
    rows = P.ladder(root=tmp_path)
    lad = {int(r["level"]): float(r["pnl"]) for r in _csv("ladder.csv")}
    s = P.summary(rows)
    assert [round(s[f"pnl{k}"][0], 2) for k in (2, 3, 4)] == [lad[2], lad[3], lad[4]]


def test_named_result_numbers():
    lad = {int(r["level"]): r for r in _csv("ladder.csv")}
    assert [round(float(lad[k]["pnl"])) for k in (2, 3, 4)] == [228, -12, -102]
    assert [round(float(lad[k]["se"])) for k in (2, 3, 4)] == [29, 13, 18]
    assert [round(float(lad[k]["fills"])) for k in (2, 3, 4)] == [841, 333, 434]
    ses = _csv("sessions.csv")
    gap = [float(r["pnl3"]) - float(r["pnl4"]) for r in ses]
    assert len(ses) == 20 and all(g > 0 for g in gap) and round(sum(gap) / 20) == 90
    sd = (sum((g - sum(gap) / 20) ** 2 for g in gap) / 19) ** 0.5
    assert round(sd / 20 ** 0.5, 1) == 7.4
    assert sum(float(r["pnl3"]) > 0 for r in ses) == 9 and sum(float(r["pnl4"]) > 0 for r in ses) == 1
    dec = {r["part"]: r for r in _csv("decomposition.csv")}
    assert [round(float(dec[k][c])) for k, c in (("shared fills", "n_replay"), ("replay-only fills", "n_replay"),
                                                ("reactive-only fills", "n_reactive"))] == [193, 140, 241]
    div = _csv("divergence.csv")
    times = sorted(float(r["first_time"]) for r in div)
    assert max(int(r["first_fill_index"]) for r in div) == 4 and round((times[9] + times[10]) / 2) == 11
    sh3, sh4 = float(dec["shared fills"]["replay"]), float(dec["shared fills"]["reactive"])
    o3, o4 = float(dec["replay-only fills"]["replay"]), float(dec["reactive-only fills"]["reactive"])
    assert (round(sh3, 1), round(sh4, 1), round(o3, 2), round(o4, 1)) == (17.5, 18.3, 0.03, -69.2)
    mgap = sh3 + o3 - sh4 - o4
    assert round(mgap, 1) == 68.4 and round(-o4 / mgap * 100) == 101 and round(90 - mgap) == 22


def test_trend_levels(tmp_path):
    t = P.trend_levels(tmp_path)
    assert (round(100 * t["level1"], 1), round(100 * t["level2"], 1)) == (-26.5, -31.5)
    d = P.B.DataAccess(tmp_path / "data")
    tab = d.get(d.daily())
    c, o = tab["close"].to_numpy(), tab["open"].to_numpy()
    w = P.Trend().targets(c)
    assert int((np.diff(w) != 0).sum()) == 57
    # the level-2 result is the level-1 rule with the position changed at the next open instead of the close
    approx = np.prod((1 + np.r_[0, w[:-2]] * (o[1:] / c[:-1] - 1)) * (1 + w[:-1] * (c[1:] / o[1:] - 1))) - 1
    assert abs(approx - t["level2"]) < 0.005


@pytest.mark.reference
def test_exercise_7_inventory_limit(tmp_path):
    d = P.B.DataAccess(tmp_path)
    out = {}
    for lim in (3, 10):
        r = P.one_session(d, None, 3, 3600.0, limit=lim)
        gap = r["shared3"] + r["only3"] - r["shared4"] - r["only4"]
        out[lim] = (r["pnl2"], r["pnl3"], r["pnl4"], r["fills2"], r["fills3"], r["fills4"], round(-r["only4"] / gap * 100))
    assert out[3] == (417.0, -95.5, -246.0, 1462, 583, 690, 129)
    assert out[10] == (350.0, -110.0, -472.0, 1580, 670, 818, 147)
