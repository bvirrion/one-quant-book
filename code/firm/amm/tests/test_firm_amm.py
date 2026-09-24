"""Acceptance tests of the Book 3, Chapter 20 build (AMM library, integer fixed point)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_amm import (
    Q96,
    amounts_for_liquidity,
    cp_amount_in,
    cp_amount_out,
    next_sqrt_price_from_amount0,
    sqrt_price_x96,
    ss_amount_out,
    ss_get_d,
    ss_get_y,
    tick_at_price,
)

E18 = 10**18


def test_constant_product():
    out = cp_amount_out(10 * E18, 1_000 * E18, 3_000_000 * E18)
    assert out == 10 * E18 * 9_970 * 3_000_000 * E18 // (1_000 * E18 * 10_000 + 10 * E18 * 9_970)
    assert cp_amount_in(out, 1_000 * E18, 3_000_000 * E18) in (10 * E18, 10 * E18 + 1)
    k0 = 1_000 * E18 * 3_000_000 * E18
    assert (1_010 * E18) * (3_000_000 * E18 - out) > k0          # the fee grows the invariant


def test_ticks_and_amounts():
    assert tick_at_price(1.0) == 0 and tick_at_price(1.0001) in (0, 1)
    assert sqrt_price_x96(0) == Q96
    sa, sb = sqrt_price_x96(-1_000), sqrt_price_x96(1_000)
    a0, a1 = amounts_for_liquidity(10**6 * E18, Q96, sa, sb)
    assert abs(a0 - a1) / a1 < 1e-9                              # symmetric range at price 1
    assert amounts_for_liquidity(E18, sa, sa, sb)[1] == 0          # at the lower edge: all token0
    assert amounts_for_liquidity(E18, sb, sa, sb)[0] == 0


def test_next_price_moves_down_when_token0_added():
    sp = sqrt_price_x96(0)
    new = next_sqrt_price_from_amount0(sp, 10**6 * E18, 10**3 * E18)
    assert new < sp and abs(new / Q96 - 1 / (1 + 1e-3)) < 1e-9


def test_stableswap():
    xp = [1_000_000 * E18, 1_000_000 * E18]
    assert ss_get_d(xp, 100) == 2_000_000 * E18
    y = ss_get_y(0, 1, xp[0] + 1_000 * E18, xp, 100)
    assert xp[1] - y < 1_000 * E18 and xp[1] - y > 999 * E18       # near one for one at balance
    cp = cp_amount_out(100_000 * E18, xp[0], xp[1], 0)
    assert ss_amount_out(0, 1, 100_000 * E18, xp, 100, 0) > cp       # far less slippage than x y = k


def test_twin_numbers():
    """The Rust twin asserts the same value (six-decimal units)."""
    e6 = 10**6
    assert ss_amount_out(0, 1, 90_000 * e6, [1_000_000 * e6, 1_200_000 * e6], 85, 4) == 90_069_485_445
