"""Acceptance tests of the Chapter 10 build."""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_execquality import Fill, report, score, size_bucket


def test_the_single_fill_of_the_chapter():
    f = Fill(0, "ABC", +1, 100, 200_180, 200_000, 200_200)       # bought at 20.018 on 20.00 x 20.02
    s = score(f, mid2_later=2 * 200_130)                          # mid 20.013 five minutes later
    assert s["improvement"] == 20                                  # 0.2 cent
    assert (s["effective2"], s["realised2"], s["impact2"]) == (160, 100, 60)   # 0.8, 0.5, 0.3 cent (doubled)


def test_identity_on_random_fills():
    rng = np.random.default_rng(10)
    for _ in range(2_000):
        bid = int(rng.integers(100_000, 900_000))
        f = Fill(0, "X", int(rng.choice([-1, 1])), 100, bid + int(rng.integers(0, 200)), bid, bid + 200)
        s = score(f, 2 * bid + int(rng.integers(-500, 700)))
        assert s["effective2"] == s["realised2"] + s["impact2"]


def test_means_are_share_weighted_and_exclusions_counted():
    fills = [Fill(0, "X", +1, 100, 100_100, 100_000, 100_100),      # at the offer: effective 0.5 c
             Fill(0, "X", +1, 300, 100_060, 100_000, 100_100),      # improved: effective 0.1 c
             Fill(0, "X", +1, 100, 100_100, 100_100, 100_000)]      # crossed quote: excluded
    r = report(fills, lambda sym, ts: 200_100, horizon=1, by=("symbol",))
    g = r[("X",)]
    assert r["_excluded"] == 1 and g["fills"] == 2 and g["shares"] == 400
    expected = (100 * 100 + 300 * 20) / 400 / 200_100 * 1e4         # doubled half-spreads over doubled mid
    assert g["effective_bp"] == pytest.approx(expected)
    assert g["inside"] == 0.75 and g["at"] == 0.25


def test_size_buckets():
    assert [size_bucket(q) for q in (1, 99, 100, 1999, 5000)] == ["1-99", "1-99", "100-499", "500-1999", "5000+"]
