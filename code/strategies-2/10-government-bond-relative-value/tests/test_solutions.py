"""Numbers gate: every numerical answer printed in Book 9, chapter 10 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_bondrv import decay, real, table  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_books():
    got = {k: (r(v["gross_sr"]), r(v["net_sr"]), r(v["mean"], 1), r(v["cost"], 1), r(v["vol"], 1), r(v["turnover"], 0))
           for k, v in table().items()}
    assert got == {"none": (0.36, 0.25, 24.4, 7.3, 67.4, 29.0), "dv01": (3.46, 1.13, 11.1, 7.3, 3.2, 29.0),
                   "factors": (5.41, 0.69, 9.8, 8.3, 1.8, 33.0)}
    assert {k: r(v["net_sr"]) for k, v in table(0.1).items()} == {"none": 0.32, "dv01": 2.54, "factors": 3.48}


def test_decay():
    d = decay()
    assert {h: (r(v["slope"]), r(v["planted"]), r(v["fast"])) for h, v in d.items() if h != "half_life_ar1"} == {
        1: (0.96, 0.99, 0.98), 5: (0.93, 0.95, 0.92), 20: (0.81, 0.83, 0.71), 60: (0.59, 0.6, 0.35),
        120: (0.4, 0.42, 0.12)}
    assert r(d["half_life_ar1"], 1) == 17.9


def test_real():
    x = real()
    assert (x["first"], x["last"], x["days"], round(100 * float(x["pc1_share"]), 1), round(100 * float(x["pc2_share"]), 1),
            round(100 * float(x["pc3_share"]), 1)) == ("1994-01-03", "2026-09-23", "8187", 87.9, 8.2, 2.0)
    assert (r(float(x["fly_mean"]), 1), r(float(x["fly_sd"]), 1), r(float(x["fly_phi"]), 4), r(float(x["fly_half_life"]), 0),
            r(float(x["fly_min"]), 0), r(float(x["fly_max"]), 0)) == (-1.6, 26.6, 0.9934, 105.0, -79.0, 74.0)
    assert r(math.log(0.5) / math.log(0.5 ** (1 / 40)), 0) == 40.0


def test_exercises():
    assert round((2 * 4.99 - 4.85 - 5.11) * 100, 1) == 2.0
