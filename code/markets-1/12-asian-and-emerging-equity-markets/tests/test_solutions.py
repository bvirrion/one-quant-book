"""Numbers gate: every numerical answer printed in the Chapter 12 text and solutions."""
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from asia_rules import autocorr, locked_days, round_to_lot, truncate


def heavy():
    return np.random.default_rng(12).standard_t(3, 60_000) * 0.035 / np.sqrt(3)


def test_text():
    assert round(math.log(1.5) / math.log(1.1), 2) == 4.25 and locked_days(0.5, 0.10) == 4
    assert round(math.log(0.5) / math.log(0.9), 2) == 6.58 and locked_days(-0.5, 0.10) == 6
    true = heavy()
    obs = truncate(true, 0.10)
    assert round(true.std() * 100, 2) == 3.45 and round(obs.std() * 100, 2) == 3.03
    assert round(autocorr(obs), 3) == 0.088 and round((np.abs(obs) > 0.0999).mean() * 100) == 2
    o = truncate(np.array([0.35, 0, 0, 0, 0]), 0.10)
    assert np.prod(1 + o) == pytest.approx(1.35)
    assert (5 + 0) / 5 == 1 and (20 + 5) / 5 == 5


def test_exercises():
    assert round(24 * 1.1, 2) == 26.40 and round(24 * 0.9, 2) == 21.60
    n = round_to_lot(250_000 / 61.30, 500)
    assert n == 4000 and round(n * 61.30) == 245_200 and round(n * 61.30 * 0.001, 2) == 245.20
    assert 5e6 * 0.001 * 2 == 10_000 and 20e6 * 0.0005 == 10_000 and 400_000 * 0.0015 == 600
    assert [locked_days(-0.35, L) for L in (0.10, 0.20, 0.05)] == [4, 1, 8]
    assert 6 / 4 == 1.5 and 26 / 4 == 6.5 and 40 - 6 == 34 and 40 - 26 == 14
    true = heavy()
    got = [(round(truncate(true, L).std() * 100, 2), round(autocorr(truncate(true, L)), 3)) for L in (0.05, 0.10, 0.20)]
    assert got == [(2.6, 0.195), (3.03, 0.088), (3.26, 0.033)]


def test_problem():
    fv = 29 / (1 + 0.04 * 0.25)
    assert round(fv, 2) == 28.71
    c, lims = 20.0, []
    for _ in range(4):
        c = math.floor(c * 1.1 * 100 + 1e-9) / 100
        lims.append(c)
    assert lims == [22.0, 24.2, 26.62, 29.28] and locked_days(fv / 20 - 1, 0.10) == 3
    assert round((fv / 22 - 1) * 100, 1) == 30.5 and round((fv - 22) * 100_000, -3) == 671_000
    closes = [20.0, 22.0, 24.2, 26.62, fv]
    r = np.array([closes[i + 1] / closes[i] - 1 for i in range(4)])
    assert [round(x, 3) for x in r] == [0.1, 0.1, 0.1, 0.079]
    ss, tot = float((r * r).sum()), fv / 20 - 1
    assert round(ss, 4) == 0.0362 and round(tot * tot, 4) == 0.1898
    assert round(math.sqrt(ss / 20) * 100, 1) == 4.3 and round(math.sqrt(tot * tot / 20) * 100, 1) == 9.7
    assert round(float((r[1:] * r[:-1]).sum() / (r * r).sum()), 2) == 0.77
    g = 29 / 28.6 - 1
    assert round(g * 100, 2) == 1.40 and round(g * 4 * 100, 1) == 5.6
    assert round((g - 0.001 - 0.01) * 100, 2) == 0.30
    assert int(2e6 / 28.6 // 100) * 100 == 69_900
