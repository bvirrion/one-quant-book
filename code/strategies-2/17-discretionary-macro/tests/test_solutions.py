"""Numbers gate: every numerical answer printed in Book 9, chapter 17 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_macrobook import premiums, stops, table  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def pct(x, d=1):
    return round(100 * float(x), d)


def test_table():
    t = table()
    assert pct(t.pop("share_right")) == 73.4
    got = {k: (r(v["mean"]), r(v["sd"]), pct(v["p_profit"], 0), pct(v["lose_when_right"]), r(v["p05"])) for k, v in t.items()}
    assert got == {"futures": (0.39, 0.63, 73.0, 0.0, -0.65), "futures, stop 25": (1.68, 2.98, 54.0, 26.5, -1.0),
                   "futures, stop 50": (0.98, 1.55, 69.0, 5.6, -1.0), "option at the money": (1.26, 2.23, 61.0, 17.2, -1.0),
                   "option out of the money": (1.69, 3.2, 54.0, 26.5, -1.0), "option spread": (0.71, 1.22, 65.0, 10.8, -1.0)}


def test_stops_premiums_and_exact_view():
    assert {d: pct(s) for d, s in stops().items()} == {10: 55.6, 25: 26.5, 50: 5.6, 75: 0.7, 100: 0.1}
    p = premiums()
    assert (r(p["atm"], 1), r(p["otm"], 1), r(p["spread"], 1)) == (27.9, 17.2, 18.2)
    t = table(0.0)
    assert (pct(t["share_right"]), r(t["futures, stop 25"]["mean"]), r(t["option at the money"]["mean"])) == (78.6, 1.45, 1.07)


def test_exercises():
    import math
    p = premiums()
    assert r(99 * math.sqrt(0.5) / math.sqrt(2 * math.pi), 1) == 27.9 and r(50 / p["spread"] - 1) == 1.75
    t = table(0.0)
    assert (r(t["futures, stop 50"]["mean"]), r(t["option out of the money"]["mean"]), r(t["option spread"]["mean"])) == (
        0.91, 1.32, 0.79)
    assert round(100 - 78.6) == 21
