"""Acceptance tests of the Book 2, Chapter 19 build (FX option conventions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_fxsmile import (
    atm_dns,
    barrier_delta,
    delta,
    down_and_out_call,
    gk,
    quadratic_smile,
    smile_vols,
    strike_from_delta,
)

ARGS = (1.15, 0.25, 0.0368, 0.02)       # spot, T, rd (USD), rf (EUR)


def test_put_call_parity():
    s, t, rd, rf = ARGS
    c, p = gk(s, 1.16, t, rd, rf, 0.07), gk(s, 1.16, t, rd, rf, 0.07, -1)
    assert math.isclose(c - p, s * math.exp(-rf * t) - 1.16 * math.exp(-rd * t), abs_tol=1e-12)


def test_strike_from_delta_round_trips():
    s, t, rd, rf = ARGS
    for kind in ("spot", "forward", "spot_pa", "forward_pa"):
        for phi, d in ((1, 0.25), (-1, -0.25)):
            k = strike_from_delta(s, t, rd, rf, 0.07, d, phi, kind)
            assert math.isclose(delta(s, k, t, rd, rf, 0.07, phi, kind), d, abs_tol=1e-9)


def test_premium_adjusted_example():
    # Reiswich-Wystup: a 60% delta on a premium of 73,669 EUR per 1,000,000 is 52.63% premium-adjusted
    assert round(0.60 - 73_669 / 1_000_000, 4) == 0.5263


def test_atm_dns_is_delta_neutral():
    s, t, rd, rf = ARGS
    for pa, kind in ((False, "forward"), (True, "forward_pa")):
        k = atm_dns(s, t, rd, rf, 0.07, pa)
        assert math.isclose(delta(s, k, t, rd, rf, 0.07, 1, kind), -delta(s, k, t, rd, rf, 0.07, -1, kind), abs_tol=1e-12)


def test_smile():
    c, p = smile_vols(0.07, -0.012, 0.002)
    assert math.isclose(c - p, -0.012) and math.isclose((c + p) / 2 - 0.07, 0.002)
    f = quadratic_smile([(1.10, 0.08), (1.15, 0.07), (1.20, 0.075)])
    assert math.isclose(f(1.15), 0.07) and f(1.05) > f(1.10)


def test_barrier():
    s, t, rd, rf = ARGS
    assert down_and_out_call(1.12, 1.15, 1.12, t, rd, rf, 0.07) == 0.0
    assert down_and_out_call(s, 1.15, 1.12, t, rd, rf, 0.07) < gk(s, 1.15, t, rd, rf, 0.07)
    assert barrier_delta(1.1201, 1.15, 1.12, t, rd, rf, 0.07) > 0
    assert math.isclose(down_and_out_call(s, 1.15, 0.5, t, rd, rf, 0.07), gk(s, 1.15, t, rd, rf, 0.07), rel_tol=1e-9)
