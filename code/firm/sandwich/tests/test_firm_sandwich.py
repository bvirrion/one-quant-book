"""Acceptance tests of the Book 3, Chapter 22 build (sandwich simulator)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_sandwich import find_sandwiches, max_front_run, min_out, run, sandwich

E6, E18 = 10**6, 10**18
RA, RB = 15_000_000 * E6, 5_000 * E18            # USDC and ETH reserves


def test_victim_protected_by_tolerance():
    dx_v = 1_000_000 * E6
    for tol in (50, 100):
        a = max_front_run(RA, RB, dx_v, tol)
        assert run(RA, RB, dx_v, a)[0] >= min_out(RA, RB, dx_v, tol)
        assert run(RA, RB, dx_v, a + 1)[0] < min_out(RA, RB, dx_v, tol)
    assert max_front_run(RA, RB, dx_v, 100) > max_front_run(RA, RB, dx_v, 50)


def test_profit_and_loss_grow_with_tolerance():
    dx_v = 1_000_000 * E6
    s1, s2 = sandwich(RA, RB, dx_v, 50, 20 * E6, 0), sandwich(RA, RB, dx_v, 100, 20 * E6, 0)
    assert 0 < s1.gross < s2.gross and 0 < s1.victim_loss < s2.victim_loss
    assert sandwich(RA, RB, dx_v, 50, 20 * E6, 9_000).net < s1.net


def test_zero_tolerance_leaves_nothing():
    s = sandwich(RA, RB, 1_000_000 * E6, 0, 20 * E6, 0)
    assert s.front_in == 0 and s.gross == 0 and s.net == -20 * E6


def test_detection():
    block = [("A", "P", "buy"), ("V", "P", "buy"), ("A", "P", "sell"), ("X", "Q", "buy")]
    assert find_sandwiches(block) == [(0, 1, 2)]
    assert find_sandwiches([("A", "P", "buy"), ("V", "Q", "buy"), ("A", "P", "sell")]) == []
