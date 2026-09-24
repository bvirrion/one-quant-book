"""Unit tests of the Chapter 3 teaching module."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_blackscholes import CASE, bs, mc_price, pde_residual, replicate_path


def test_mc_is_unbiased_over_seeds():
    f = bs(CASE["spot"], CASE["strike"], CASE["t"], CASE["r"], CASE["q"], CASE["vol"], "C")
    z = [(mc_price(20_000, seed=s)[0] - f) / mc_price(20_000, seed=s)[1] for s in range(40)]
    assert abs(np.mean(z)) < 0.5 and 0.6 < np.std(z) < 1.4


def test_antithetic_reduces_error():
    assert mc_price(50_000, antithetic=True)[1] < mc_price(50_000)[1]


def test_pde_holds_for_other_parameters():
    assert abs(pde_residual({"spot": 80.0, "strike": 95.0, "t": 0.3, "r": 0.02, "q": 0.03, "vol": 0.4})) < 1e-12


def test_hedging_error_shrinks_with_rebalancing():
    errs = {n: np.mean([abs(replicate_path(seed=s, steps=n)[3][-1] - replicate_path(seed=s, steps=n)[2][-1])
                        for s in range(20)]) for n in (52, 832)}
    assert errs[832] < 0.5 * errs[52]
