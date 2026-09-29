"""Numbers gate: every numerical answer printed in Book 16, chapter 18 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_docs as m  # noqa: E402

dt = m.dt


def r(x, d=1):
    return round(float(x), d)


def test_hand_annex():
    a = dt.Annex(2.0, 0.5, 0.1, 0.0, {"cash": 0.0})
    assert r(dt.call(a, 10.37, {"cash": 5.0})) == 3.4 and dt.call(a, 6.8, {"cash": 5.0}) == 0.0
    assert dt.call(a, 2.3, {"cash": 0.0}) == 0.0
    assert r(dt.call(m.ANNEXES["dealer A"], 4.2, {"cash": 3.0, "bonds": 5.0})) == 1.3


def test_nav_and_trips():
    n = m.nav_path()
    assert (r(n.max()), int(n.argmax()), r(n.min()), int(n.argmin()), r(n[-1])) == (447.7, 45, 247.7, 204, 301.9)
    assert r(100 * (n.min() / n.max() - 1)) == -44.7
    t = m.trips()
    assert {k: v[0] for k, v in t.items()} == {"prime broker 1": 150, "prime broker 2": 177, "dealer A": 180, "dealer B": 137}
    assert [v[1] for v in t.values()] == ["fall of 15% over 21 days", "fall of 30% over 63 days", "below floor 280",
                                          "fall of 12% over 21 days"]
    assert [(r(n[d]), r(100 * (n[d] / n[d - 21] - 1)), r(100 * (n[d] / n[d - 63] - 1))) for d in (137, 150, 177, 180)] == [
        (369.3, -12.4, -12.5), (338.0, -15.0, -17.6), (288.3, -9.6, -30.6), (275.2, -10.1, -33.2)]


def test_calls_and_close_out():
    c = m.calls()
    assert {k: (r(v.sum()), int((v > 0).sum()), int((v < 0).sum())) for k, v in c.items()} == {
        "dealer A": (12.4, 44, 43), "dealer B": (1.9, 19, 20), "dealer C": (0.0, 0, 0)}
    assert r(m.exposures()["dealer C"].max(), 2) == 0.02
    x = m.close_out_first()
    assert (x["dealer"], x["day"], r(x["exposure"], 2), r(x["posted"], 2)) == ("dealer B", 137, 2.84, 1.2)
    assert r(x["with"]["balances"]["swaps"], 2) == 4.64 and r(x["with"]["net"], 2) == -1.36
    assert x["without"]["net"] is None and r(x["without"]["gross_claims"], 2) == 4.64


def test_small_runs():
    assert dt.first_trip(np.array([100.0, 99.0, 98.0]), dt.Trigger("x", ((1, 0.5),))) is None
    assert dt.first_trip(np.array([100.0, 40.0]), dt.Trigger("x", ((1, 0.5),))) == (1, "fall of 50% over 1 days")


def test_exercises():
    n = m.nav_path()
    assert r(100 * (1 - n[137] / n.max())) == 17.5 and 180 - 137 == 43
    t = dt.Trigger("pb2", ((21, 0.20), (63, 0.20), (252, 0.40)))
    assert dt.first_trip(n, t) == (151, "fall of 20% over 63 days")
    assert r(dt.call(dt.Annex(2.0, 0.5, 0.1, 0.0, {"cash": 0.0}), 10.37, {})) == 8.4
    c, ex = m.calls(), m.exposures()
    assert (np.cumsum(c["dealer A"]) > ex["dealer A"]).all()
