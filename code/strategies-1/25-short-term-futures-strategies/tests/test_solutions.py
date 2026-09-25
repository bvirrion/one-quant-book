"""Numbers gate: every numerical answer printed in Book 8, chapter 25 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_futures import announcement_path, announcements, fade_table, orb_table, sessions, tape_cost  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_sessions_and_cost():
    S = sessions()
    day = S["r"].sum(1) + S["gap"]
    assert (r(100 * day.std() * math.sqrt(252), 1), int(S["ann"].sum())) == (16.2, 79)
    half, spread = tape_cost()
    assert (r(spread, 2), r(half, 2)) == (1.08, 0.54)


def test_orb_and_fade():
    assert {w: tuple(r(x) for x in v) for w, v in orb_table().items()} == \
        {15: (0.56, 0.35, 1.88), 30: (0.77, 0.55, 2.77), 60: (1.49, 1.25, 5.62)}
    assert {z: tuple(r(x) for x in v) for z, v in fade_table().items()} == \
        {1.5: (3.78, -3.31), 2.0: (2.86, -1.5), 2.5: (1.82, -0.71), 3.0: (0.59, -0.78)}


def test_announcements():
    a = announcements()
    assert {k: (v["n"], r(v["bp"], 1), r(v["t"], 1), r(v["sr"], 2)) for k, v in a.items()} == \
        {"before": (39, 40.6, 2.7, 1.21), "after": (40, 18.8, 1.3, 0.58)}
    p, k = announcement_path()
    assert (k, r(p["before"][k - 1], 1), r(p["after"][k - 1], 1)) == (466, 41.7, 19.9)


def test_exercises():
    assert r(0.01 / 100 * 1e4, 1) == 1.0 and r(2 * 0.54, 2) == 1.08
    assert r(50 * 0.3, 0) == 15 and r(math.sqrt(252 / 32), 2) == 2.81
    se = 1.0 / math.sqrt(39)
    assert r(se * 100, 0) == 16 and r(0.5 / se, 1) == 3.1
    assert r(np.sqrt(0.25 + 0.75 * 0.81), 3) == 0.926


def test_fade_break_even():
    from s1_futures import fade_stats
    g, n, be = fade_stats(2.0)
    assert (r(g), r(n, 1), r(be)) == (5.18, 7.3, 0.35)
    assert r(0.1 * math.sqrt(2 / math.pi) / math.sqrt(1.01), 2) == 0.08
