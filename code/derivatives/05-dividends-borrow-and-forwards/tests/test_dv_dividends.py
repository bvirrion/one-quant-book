"""Unit tests of the Chapter 5 teaching module."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_dividends import ONE, escrowed_call, proportional_call, spot_call


def test_escrowed_equals_proportional_for_europeans():
    for k in (80, 100, 120):
        assert abs(escrowed_call(k) - proportional_call(k)) < 1e-12


def test_spot_model_without_dividend_is_black_scholes():
    no_div = {**ONE, "div": 0.0}
    assert abs(spot_call(100, no_div) - escrowed_call(100, no_div)) < 1e-9


def test_quadrature_converged():
    assert abs(spot_call(100, n=64) - spot_call(100, n=128)) < 1e-8
