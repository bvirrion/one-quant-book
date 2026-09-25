"""Acceptance tests of firm.lobfeat (the Python reference; cpp/ and rust/ replay the same fixture)."""
import csv
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tape"))
from firm_lobfeat import Engine, bucket, run
from firm_tape import TapeConfig, simulate

HERE = pathlib.Path(__file__).resolve().parents[1]


def test_hand_checked_ofi_and_imbalance():
    e = Engine(levels=2)
    assert e.on("A", 1, 1, 99, 100) is None                  # one side only: no features yet
    f = e.on("A", 2, -1, 100, 100)
    assert (f.bid, f.ask, f.imbalance, f.ofi) == (99, 100, 0.0, 0)
    f = e.on("A", 3, 1, 99, 200)                             # bid queue grows by 200
    assert f.ofi == 200 and np.isclose(f.imbalance, 0.5) and np.isclose(f.wmid, (100 * 300 + 99 * 100) / 400)
    f = e.on("E", 2, -1, 100, 50)                            # an execution against the ask removes 50
    assert f.ofi == 50 and f.ofi_cum == 250
    f = e.on("X", 2, -1, 100, 50)                            # the ask queue empties: no ask left
    assert f is None
    f = e.on("A", 4, -1, 101, 30)                            # the ask moves up a tick
    assert f.ofi == 50 and f.ask == 101                      # the ask rose: + the last recorded ask size (50)
    assert bucket(-1.0, 10) == 0 and bucket(1.0, 10) == 9 and bucket(0.0, 10) == 5


def test_fixture_matches_the_reference():
    d = HERE / "data"
    g = [float(r["g"]) for r in csv.DictReader(open(d / "fixture_g.csv"))]
    msgs = simulate(TapeConfig(seconds=120.0, news_at=None, seed=21)).msgs[:3000]
    out = run(msgs, 5, g)
    rows = list(csv.DictReader(open(d / "fixture_expected.csv")))
    assert len(rows) == len(msgs)
    for i in range(0, len(rows), 97):
        if rows[i]["bid"] == "nan":
            assert np.isnan(out["bid"][i])
            continue
        assert out["ofi_cum"][i] == int(rows[i]["ofi_cum"]) and out["micro"][i] == float(rows[i]["micro"])


def test_features_are_bounded_and_ofi_tracks_the_mid():
    tp = simulate(TapeConfig(seconds=900.0, news_at=None, seed=4))
    out = run(tp.msgs)
    ok = ~np.isnan(out["imbalance"])
    assert (np.abs(out["imbalance"][ok]) <= 1).all() and (np.abs(out["depth_imbalance"][ok]) <= 1).all()
    mid = 0.5 * (out["bid"] + out["ask"])
    t = tp.msgs["t"]
    grid = np.searchsorted(t, np.arange(10.0, 900.0, 10.0))
    dm, dofi = np.diff(mid[grid]), np.diff(out["ofi_cum"][grid])
    assert np.corrcoef(dm, dofi)[0, 1] > 0.4
