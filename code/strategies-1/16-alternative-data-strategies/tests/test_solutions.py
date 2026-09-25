"""Numbers gate: every numerical answer printed in Book 8, chapter 16 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_altstrat import nowcast_quality, run  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_nowcast():
    q = nowcast_quality()
    assert (r(q["corr"]), r(q["slope"]), q["events"]) == (0.46, 0.21, 4162)


def test_decay():
    got = [(r(run(p)["sr_net"]), r(100 * run(p)["ret_net"], 1)) for p in (0.0, 0.25, 0.5, 0.75, 0.9)]
    assert got == [(4.41, 61.1), (3.2, 42.6), (1.86, 24.2), (0.45, 5.7), (-0.43, -5.4)]
    assert (r(run(0.0)["sr_gross"]), r(run(0.0)["turnover"], 1)) == (4.94, 36.3)
    assert [(r(run(p, 1)["sr_net"]), r(100 * run(p, 1)["ret_net"], 1)) for p in (0.5, 0.9)] == [(4.43, 55.9), (4.29, 55.6)]


def test_exercises():
    x = run(0.5, 0, 3.0)
    assert (r(x['sr_net']), r(100 * x['ret_net'], 1), r(run(0.0, 0, 3.0)['sr_net'])) == (1.35, 17.6, 3.2)
    assert r(4162 / ((2520 - 10) / 252), 0) == 418
    assert r(1 / math.sqrt(1 + 2.0**2), 2) == 0.45 and r(1 / (1 + 2.0**2), 2) == 0.2
    assert r(100 * 3 * 0.016 * 0.2 * 2, 2) == 1.92 and r(0.5 * 1.92, 2) == 0.96
