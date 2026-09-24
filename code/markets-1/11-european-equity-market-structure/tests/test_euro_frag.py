import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from euro_frag import cap_usage, ebbo, effective_venues, herfindahl, simulate_cap


def test_herfindahl_limits():
    assert herfindahl([100]) == 1.0 and herfindahl([1, 1, 1, 1]) == pytest.approx(0.25)
    assert effective_venues([1, 1, 1, 1]) == pytest.approx(4.0)
    assert effective_venues([60, 20, 10, 10]) == pytest.approx(1 / 0.42)


def test_ebbo_pools_venues_without_a_size_filter():
    b, a, bv, av = ebbo({"XPAR": (45.20, 45.24), "CEUX": (45.21, 45.23), "AQEU": (45.21, 45.24)})
    assert (b, a, bv, av) == (45.21, 45.23, ["AQEU", "CEUX"], ["CEUX"])


def test_cap_usage_is_a_rolling_ratio():
    u = cap_usage(np.full(14, 8.0), np.full(14, 100.0))
    assert len(u) == 3 and np.allclose(u, 0.08)


def test_suspension_empties_the_dark_book_for_three_months():
    s = simulate_cap()
    breaches = [m for m in range(11, 36) if s["usage"][m] > 0.07 and s["dark"][m] > 0]
    assert breaches, "the scenario is built to breach the cap"
    first = breaches[0]
    assert all(s["dark"][first + k] == 0 for k in (1, 2, 3)) and s["dark"][first + 4] > 0
    assert s["periodic"][first + 1] / s["total"][first + 1] > s["periodic"][first] / s["total"][first]
