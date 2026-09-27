"""Numbers gate: every numerical answer printed in Book 10, chapter 25 (text and solutions)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_halts import CRASH_QTY, magnet_study, mechanisms_study  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_mechanisms():
    s = mechanisms_study()
    got = [(r(s[k]["fall"]), r(s[k]["halted"], 0), round(s[k]["filled"]), r(s[k]["cost"])) for k in
           ("none", "LULD", "velocity", "market-wide")]
    assert got == [(27.4, 0, 17580, 12.2), (20.0, 0, 16440, 9.6), (24.9, 79, 11752, 13.2), (18.9, 48, 9279, 6.6)]
    assert [r(100 * s[k]["filled"] / CRASH_QTY) for k in ("none", "LULD", "velocity", "market-wide")] == [
        43.9, 41.1, 29.4, 23.2]


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_magnet_named_result():
    m = magnet_study()
    both, band, none = m["band and anticipators"], m["band alone"], m["no band"]
    assert (r(both[5][1], 2), r(band[5][1], 2), r(none[5][1], 2)) == (0.66, 0.63, 0.75)
    assert (r(m["magnet"], 2), r(m["blocking"], 2)) == (0.03, -0.12)
    assert (r(both[5][2], 2), r(band[5][2], 2)) == (0.05, 0.06)
    assert sum(both[x][1] > band[x][1] for x in both) == 9 and sum(band[x][1] < none[x][1] for x in band) == 10
    # exercise 7, at 3 ticks
    se = math.sqrt(both[3][2] ** 2 + band[3][2] ** 2)
    se2 = math.sqrt(band[3][2] ** 2 + none[3][2] ** 2)
    assert (r(both[3][1], 3), r(band[3][1], 3), r(none[3][1], 3), r(se, 2), r(se2, 2)) == (0.727, 0.694, 0.816, 0.09, 0.09)
    assert (r(both[3][1] - band[3][1], 2), r(band[3][1] - none[3][1], 2)) == (0.03, -0.12)


def test_exercise_1():
    assert (int(999_300 * 0.9985) // 100 * 100, -(-int(999_300 * 1.0015) // 100) * 100) == (997_800, 1_000_800)


def test_small_runs():
    # One crash instead of twenty per mechanism: without a mechanism nothing halts, the pauses do halt, and every
    # mechanism leaves part of the crash order unfilled at worst.
    s = mechanisms_study(seeds=(1,))
    assert s["none"]["halted"] == 0.0 and max(s["velocity"]["halted"], s["market-wide"]["halted"]) > 0
    assert all(0 < v["filled"] <= CRASH_QTY and v["fall"] > 0 for v in s.values())
