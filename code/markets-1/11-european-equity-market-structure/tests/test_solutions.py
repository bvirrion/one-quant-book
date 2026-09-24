"""Numbers gate: every numerical answer printed in the Chapter 11 text and solutions."""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from euro_frag import ebbo, effective_venues, herfindahl, simulate_cap


def test_text():
    assert herfindahl([60, 20, 10, 10]) == pytest.approx(0.42) and round(effective_venues([60, 20, 10, 10]), 1) == 2.4
    assert herfindahl([40, 20, 20, 20]) == pytest.approx(0.28) and round(effective_venues([40, 20, 20, 20]), 1) == 3.6
    assert ebbo({"XPAR": (45.20, 45.24), "A": (45.21, 45.23), "B": (45.21, 45.24)})[:2] == (45.21, 45.23)
    s = simulate_cap()
    first = [m + 1 for m in range(11, 36) if s["usage"][m] > 0.07 and s["dark"][m] > 0][0]
    assert first == 28 and all(s["dark"][first + k - 1] == 0 for k in (1, 2, 3))
    assert round(s["periodic"][first] / s["total"][first] * 100) == 12
    assert round(57.5 / 80 * 100) == 72 and 52.8 < 57.5


def test_exercises():
    assert herfindahl([45, 25, 15, 10, 5]) == pytest.approx(0.30) and round(effective_venues([45, 25, 15, 10, 5]), 2) == 3.33
    assert [round(57.5 * x, 1) for x in (0.243, 0.104, 0.109)] == [14.0, 6.0, 6.3] and round(80 - 57.5 - 14.3, 1) == 8.2
    assert ebbo({"X": (18.340, 18.360), "Y": (18.345, 18.355), "Z": (18.350, 18.365)}) == (18.350, 18.355, ["Z"], ["Y"])
    assert 0.07 * 4800 - 300 == pytest.approx(36) and 36 / 400 == 0.09
    assert round(0.01 / 12.40 * 1e4, 1) == 8.1
    firsts = []
    for seed in range(50):
        r = simulate_cap(seed=seed)
        b = [m + 1 for m in range(11, 36) if r["usage"][m] > 0.07 and r["dark"][m] > 0]
        firsts.append(b[0] if b else None)
    assert np.median([x for x in firsts if x]) == 28 and sum(x is None for x in firsts) == 0


def test_problem():
    assert 500 * 21 == 10_500 and 10_500 * 0.075 == 787.5
    assert effective_venues([60, 10, 10, 10, 10]) == pytest.approx(2.5)
    mech = [38, 20, 27, 7.5, 4, 3.5]
    assert sum(mech) == 100 and round(herfindahl(mech), 3) == 0.266 and round(effective_venues(mech), 2) == 3.76
    d = 7.5
    new = [38 + 0.2 * d * 38 / 65, 20, 27 + 0.2 * d * 27 / 65, 4 + 0.45 * d, 3.5 + 0.25 * d]
    assert [round(x, 2) for x in new] == [38.88, 20, 27.62, 7.38, 5.38] and sum(new) == pytest.approx(99.25)
    nn = [x / sum(new) * 100 for x in new]
    assert [round(x, 1) for x in nn] == [39.2, 20.2, 27.8, 7.4, 5.4]
    assert round(nn[3] - 4, 1) == 3.4 and round(effective_venues(nn), 2) == 3.57
    lost = 40e6 * 0.12 * (1 - 0.45 - 0.25)
    assert lost == pytest.approx(1.44e6) and round(lost * 0.0002 * 21) == 6048
    assert 9 * 7.5 / 12 == 5.625 and 11 * 7.5 / 12 == 6.875 and 12 * 7.5 / 12 == 7.5
