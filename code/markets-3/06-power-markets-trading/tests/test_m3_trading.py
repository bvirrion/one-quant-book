"""Tests of the Chapter 6 teaching module (Book 3): the battery optimiser against brute force."""
import itertools
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from m3_trading import battery_plan


def brute(prices, cycles=1):
    eta, best = math.sqrt(0.88), 0.0
    for acts in itertools.product((-1, 0, 1), repeat=len(prices)):
        soc, ch, cash, ok = 0, 0, 0.0, True
        for p, a in zip(prices, acts, strict=True):
            soc += a
            ch += a == 1
            if not 0 <= soc <= 2 or ch > 2 * cycles:
                ok = False
                break
            cash += -p * 100 / eta if a == 1 else p * 100 * eta if a == -1 else 0.0
        if ok and soc == 0:
            best = max(best, cash)
    return best


def test_dp_matches_brute_force():
    for prices in ([50, 10, 5, 80, 90, 20, 70], [-10, 100, -5, 60, 0, 120, 30], [40, 40, 40, 40, 40, 40]):
        assert math.isclose(battery_plan(prices)[0], brute(prices), abs_tol=1e-6)
        assert math.isclose(battery_plan(prices, 2)[0], brute(prices, 2), abs_tol=1e-6)
