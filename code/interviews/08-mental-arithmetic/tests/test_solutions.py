"""Numbers gate: every numerical answer printed in Book 18, chapter 8 (text and solutions)."""
import math
import pathlib
import sys
from fractions import Fraction

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_arith import (
    digit_sum_mod9,
    doubling_exact,
    doubling_rule,
    ln1p_series,
    nines_check,
    rate_where_rule_exact,
    sqrt_linear,
)


def test_hook():
    assert Fraction(7, 100) * 340_000_000 / 250 == 95_200
    assert Fraction(7, 100) / 250 == Fraction(28, 100_000)  # 2.8 basis points
    assert 340 * 280 == 95_200


def test_text_examples():
    assert 43 * 37 == 40**2 - 3**2 == 1591
    assert 103 * 108 == 100 * (100 + 3 + 8) + 3 * 8 == 11124
    assert 85**2 == 8 * 9 * 100 + 25 == 7225
    assert 48 * 25 == 4800 // 4 == 1200
    assert Fraction(1, 7) == Fraction(142857, 999999)
    assert round(1 / 13, 4) == 0.0769 and round(1 / 17, 4) == 0.0588 and round(1 / 19, 4) == 0.0526
    assert Fraction(18, 100) * 50 == Fraction(50, 100) * 18 == 9
    est, bound = sqrt_linear(10, 3)
    assert est == 10.15 and round(math.sqrt(103), 4) == 10.1489 and bound < 0.0012
    assert round(doubling_exact(0.08), 2) == 9.01 and doubling_rule(0.08) == 9.0
    assert digit_sum_mod9(5824) == 1


def test_q1_to_q5():
    assert 47 * 53 == 50**2 - 3**2 == 2491
    assert 96 * 104 == 9984 and 98 * 97 == 100 * 95 + 6 == 9506
    assert 65**2 == 4225
    assert Fraction(125, 1000) * 360 == 45 and Fraction(36, 100) * 25 == 9
    assert round(3 / 7, 3) == 0.429 and round(5 / 13, 3) == 0.385


def test_q6_sqrt():
    est, bound = sqrt_linear(7, 1)
    assert round(est, 4) == 7.0714 and round(math.sqrt(50), 4) == 7.0711
    assert round(bound, 5) == 0.00036
    assert 0 < est - math.sqrt(50) < bound


def test_q7_rule72():
    assert doubling_rule(0.06) == 12 and round(doubling_exact(0.06), 1) == 11.9
    assert doubling_rule(0.01) == 72 and round(doubling_exact(0.01), 1) == 69.7
    assert doubling_rule(0.24) == 3 and round(doubling_exact(0.24), 2) == 3.22
    errs = {r: abs(doubling_rule(r) - doubling_exact(r)) / doubling_exact(r) for r in (0.01, 0.06, 0.24)}
    assert max(errs, key=errs.get) == 0.24 and round(100 * errs[0.24], 1) == 6.9
    assert round(100 * errs[0.01], 1) == 3.4


def test_q8_bp_chain():
    assert Fraction(32, 100_000) * 250_000_000 == 80_000
    assert 80_000 * 252 == 20_160_000


def test_q9_nines():
    assert 3847 * 29 == 111_563
    assert nines_check(3847, 29, 111_563)
    assert nines_check(3847, 29, 111_653)  # a transposition passes: the blind spot
    assert not nines_check(3847, 29, 111_573)


def test_q10_percent_chain():
    assert Fraction(12, 10) * Fraction(8, 10) == Fraction(96, 100)
    assert Fraction(125, 100) * Fraction(8, 10) == 1


def test_q11_log():
    s = ln1p_series(0.07)
    assert round(s, 5) == 0.06766 and round(math.log(1.07), 5) == 0.06766
    assert round(0.07 - 0.07**2 / 2, 5) == 0.06755
    assert round(math.log(2) / math.log(1.07), 2) == 10.24


def test_q12_compound():
    assert round(10 * math.log(1.03), 4) == 0.2956
    assert round(1.03**10, 3) == 1.344
    assert round(math.exp(0.3), 3) == 1.35


def test_q13_product():
    assert Fraction(625, 10_000) * Fraction(48, 10) * 125 == Fraction(75, 2)


def test_q14_rule_exact_rate():
    assert round(100 * rate_where_rule_exact(72), 2) == 7.85
    assert round(100 * rate_where_rule_exact(70), 1) == 2.0
    # continuous compounding: 69.3 is exact for continuously compounded rates
    assert round(100 * math.log(2), 1) == 69.3
    # the rule of 69.3 always underestimates for annual compounding
    assert all(doubling_rule(r, 69.3) < doubling_exact(r) for r in [i / 100 for i in range(1, 30)])


def test_extra_text_numbers():
    assert 67 * 38 == 67 * 40 - 67 * 2 == 2546
    assert 5 + 8 + 2 + 4 == 19 and 19 % 9 == 1
    assert 75**2 - 65**2 == 1400
    assert round(72 / 7, 2) == 10.29
    assert round(7 + 1 / 14 - 1 / (8 * 343), 4) == round(math.sqrt(50), 4)
    assert round(math.exp(0.3) * math.exp(-0.0044), 4) == 1.3439


def test_worked_answers():
    assert 1250 * Fraction(25, 2) == 15_625 == Fraction(10**6, 64) and 3 * 15_625 == 46_875
    assert 1000 * 10 * 3 == 30_000 and 1300 * 13 * 3 == 50_700
    g = Fraction(12)
    assert Fraction(4, 5) * (g - 2) == 8
    assert Fraction(25, 2) + 2 == Fraction(29, 2)
    x = 12 * (0.015 - 0.015**2 / 2)
    assert round(0.015 - 0.015**2 / 2, 7) == 0.0148875 and round(x, 5) == 0.17865
    assert round(1 + x + x**2 / 2 + x**3 / 6, 4) == 1.1956
    assert round(x**2 / 2, 5) == 0.01596 and round(x**3 / 6, 5) == 0.00095
    assert round(1.015**12, 5) == 1.19562
    assert round(math.comb(12, 2) * 0.015**2 * 100, 1) == 1.5
