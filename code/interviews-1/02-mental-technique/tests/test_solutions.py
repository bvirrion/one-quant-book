"""Every number printed in the answers of "Mental Technique": exact value first, then the printed approximation."""
import math
from fractions import Fraction as F

import numpy as np

NONNUMERIC = {}


def digit_root(n):
    return n % 9


def alt_sum(n):
    total, sign = 0, 1
    while n:
        total += sign * (n % 10)
        sign, n = -sign, n // 10
    return total


def test_q1():
    assert 97 * 103 == 100**2 - 3**2 == 9991
    assert 47 * 53 == 2500 - 9 == 2491
    assert 96 * 108 == 102**2 - 6**2 == 10404 - 36 == 10368
    assert 47 * 54 == 47 * 53 + 47 == 2538


def test_q2():
    assert 85**2 == 8 * 9 * 100 + 25 == 7225
    for a in range(1, 200):
        assert (10 * a + 5) ** 2 == 100 * a * (a + 1) + 25
    assert 115**2 == 11 * 12 * 100 + 25 == 13225
    assert 53**2 == 2809 and 47**2 == 2209
    assert 67**2 == 70 * 64 + 9 == 4489
    for d in range(-9, 10):
        assert (50 + d) ** 2 == 2500 + 100 * d + d**2


def test_q3():
    assert 97 * 96 == 100 * (100 - 3 - 4) + 3 * 4 == 9312
    for a in range(0, 30):
        for b in range(0, 30):
            assert (100 - a) * (100 - b) == 100 * (100 - a - b) + a * b
    assert 103 * 106 == 100 * 109 + 18 == 10918
    assert 88 * 85 == 7300 + 180 == 7480
    assert 48 * 47 == 50 * 45 + 6 == 2256


def test_q4():
    assert 368 * 125 == 368 // 8 * 1000 == 46000
    assert 372 * 125 == 46500 and F(372, 8) == F(93, 2)
    assert 368 * 375 == 138000
    assert F(3500, 125) == 28 and 3500 * 8 == 28000


def test_q5():
    assert 486 * 11 == 5346 == 4860 + 486
    # The columns printed, with their carries.
    columns = [6, 8 + 6, 4 + 8, 4]
    assert columns == [6, 14, 12, 4]
    out, carry = [], 0
    for c in columns:
        c += carry
        out.append(c % 10)
        carry = c // 10
    assert out == [6, 4, 3, 5] and carry == 0
    assert 486 * 101 == 48600 + 486 == 49086


def test_q6():
    assert F(16, 100) * 25 == F(25, 100) * 16 == 4
    assert F(18, 100) * 50 == F(50, 100) * 18 == 9
    assert F(4, 100) * 175 == F(175, 100) * 4 == 7
    assert F(36, 100) * 25 == 9
    assert F(125, 1000) * 64 == 8


def test_q7():
    assert F(384) / F(120, 100) == 320
    assert F(20, 120) == F(1, 6) and 384 * F(1, 6) == 64 and 320 + 64 == 384
    assert F(20, 100) * 384 == F(768, 10)
    assert F(25, 125) == F(1, 5)
    assert F(8, 108) == F(2, 27) and round(100 * 2 / 27, 1) == 7.4
    assert F(384) / F(8, 10) == 480 and 480 - 384 == 96 and F(96, 384) == F(1, 4)


def test_q8():
    rise = lambda d: d / (1 - d)  # noqa: E731
    assert rise(F(1, 5)) == F(1, 4)
    assert rise(F(375, 1000)) == F(3, 5)
    assert rise(F(1, 2)) == 1


def test_q9():
    assert 7 * 14 == 98 and 9 * 11 == 99
    assert F(11, 14) - F(7, 9) == F(1, 126)
    assert round(2 / 9, 3) == 0.222 and round(3 / 14, 3) == 0.214
    assert F(1, 2) > F(11, 30)
    assert 13 * 30 == 390 and 17 * 23 == 391
    assert F(23, 30) - F(13, 17) == F(1, 510)


def cycle(num, den):
    """Digits and remainders of num/den in long division, until the remainder repeats."""
    digits, rems = [], []
    r = num % den
    while r not in rems:
        rems.append(r)
        r *= 10
        digits.append(r // den)
        r %= den
    return "".join(map(str, digits)), rems


def test_q10():
    assert cycle(1, 7) == ("142857", [1, 3, 2, 6, 4, 5])
    assert cycle(3, 7)[0] == "428571"
    assert cycle(5, 7)[0] == "714285"
    for k in range(1, 7):
        d = cycle(k, 7)[0]
        assert d in "142857142857"
    assert cycle(1, 13)[0] == "076923"
    assert cycle(3, 13)[0] == "230769" and "230769" in "076923076923"
    assert cycle(2, 13)[0] == "153846" and "153846" not in "076923076923"


def test_q11():
    assert F(300 * 80 + 500 * 88, 800) == 85 == 80 + F(5, 8) * 8
    assert F(80 + 88, 2) == 84
    avg = (400 * F(1015, 10) + 100 * 102 + 500 * 101) / 1000
    assert avg == F(1013, 10)
    assert F(4, 10) * F(5, 10) + F(1, 10) * 1 == F(3, 10)


def test_q12():
    exact = math.log(2) / math.log(1.08)
    assert 72 / 8 == 9 and round(exact, 3) == 9.006
    assert round(exact * 8, 2) == 72.05
    assert round(100 * math.log(2), 1) == 69.3
    assert 100 / 8 == 12.5
    triple = math.log(3) / math.log(1.08)
    assert round(triple, 2) == 14.27 and 114 / 8 == 14.25
    assert round(triple * 8) == 114
    assert all(72 % k == 0 for k in (2, 3, 4, 6, 8, 9, 12))


def test_q13():
    assert round(math.sqrt(252), 2) == 15.87
    assert abs(16 / math.sqrt(252) - 1) < 0.01
    assert 32 / 16 == 2 and round(32 / math.sqrt(252), 2) == 2.02
    assert round(math.sqrt(52), 1) == 7.2 and round(math.sqrt(12), 2) == 3.46
    assert round(32 / math.sqrt(52), 1) == 4.4 and round(32 / math.sqrt(12), 1) == 9.2
    assert round(32 / 252, 2) == 0.13
    assert 4 / 2 == 2


def test_q14():
    assert 2**3 * 3**2 == 72
    assert round(3 * 0.301 + 2 * 0.477, 3) == 1.857
    assert round(math.log10(72), 4) == 1.8573
    assert round(1.857 - 4, 3) == -2.143 and F(72, 10**4) == F(72, 10000)
    assert round(math.log10(0.0072), 3) == -2.143
    assert round(1 - 0.301, 3) == 0.699
    assert round(0.477 - 0.301, 3) == 0.176


def test_q15():
    assert 2**10 == 1024
    assert 2**30 == 1073741824 and round(1.024**3, 3) == 1.074
    assert abs(10**9 / 2**30 - 1) < 0.07 and abs(10**9 / 2**30 - 1) > 0.065
    assert abs(2**40 / 10**12 - 1) < 0.1
    assert f"{2.0**100:.2e}" == "1.27e+30"
    assert round(1.024**6, 2) == 1.15
    assert round(2**60 / 1e18, 2) == 1.15
    assert f"{2.0**64:.1e}" == "1.8e+19"


def test_q16():
    a, d = 7, 1
    est = F(a) + F(d, 2 * a)
    assert est == 7 + F(1, 14) and round(float(est), 4) == 7.0714
    assert round(math.sqrt(50), 5) == 7.07107
    for a2, d2 in ((7, 1), (9, -1), (1.8, -0.04)):
        assert (a2 + d2 / (2 * a2)) ** 2 > a2**2 + d2
    est2 = 1.8 - 0.04 / 3.6
    assert round(est2, 3) == 1.789 and 1.8**2 - 3.24 < 1e-12
    assert round(math.sqrt(3_200_000), 1) == 1788.9
    interp = 7 + F(1, 15)
    assert round(math.sqrt(50) - float(interp), 3) == 0.004
    # A second Newton step comes far closer but stays above the root: it never reaches it.
    second = (est + 50 / est) / 2
    assert second**2 > 50 and second < est
    assert second - math.sqrt(50) < (float(est) - math.sqrt(50)) / 1000


def test_q17():
    assert 3_500_000 * F(10, 10_000) == 3500 == 100 * 10 * F(35, 10)
    assert 1_000_000 * F(1, 10_000) == 100
    assert 250_000_000 * F(1, 10_000) == 25000
    assert 25000 * F(1, 4) == 6250
    assert 250_000_000 * F(1, 100) * F(1, 4) == 625000
    assert F(1, 8) * 100 == F(25, 2)


def test_q18():
    assert 99 + F(17, 32) == F(9953125, 100000)
    assert F(1, 32) == F(3125, 100000)
    assert F(17, 32) == F(16, 32) + F(1, 32) == F(53125, 100000)
    halving = [F(1, 2**k) for k in range(1, 6)]
    assert [float(x) for x in halving] == [0.5, 0.25, 0.125, 0.0625, 0.03125]
    assert F(40625, 100000) == F(13, 32) == F(375, 1000) + F(3125, 100000) and F(12, 32) == F(375, 1000)
    assert 10_000_000 * F(3125, 100000) / 100 == 3125


def test_q19():
    assert 37 * 43 == 40**2 - 3**2 == 1591
    assert 38 * 42 == 40**2 - 2**2 == 1596
    assert 38 * 42 - 37 * 43 == 5
    assert 50 * 50 == 2500 and 49 * 51 == 2499 and 45 * 55 == 2475 and 40 * 60 == 2400


def test_q20():
    assert F(102, 100) * F(97, 100) == F(9894, 10000)
    assert 1 + F(2, 100) - F(3, 100) + F(2, 100) * -F(3, 100) == F(9894, 10000)
    assert F(99, 100) - F(9894, 10000) == F(6, 10000)
    assert F(99, 100) + F(6, 10000) == F(9906, 10000)
    a, b, c = F(2, 100), F(3, 100), -F(4, 100)
    assert 1 + a + b + c == F(101, 100)
    assert a * b + a * c + b * c == -F(14, 10000)
    assert round(float(a * b * c), 5) == -0.00002
    exact = F(102, 100) * F(103, 100) * F(96, 100)
    assert float(exact) == 1.008576 and round(float(exact), 5) == 1.00858


def test_q21():
    assert 3847 * 26 == 100022
    claim = 100122
    assert claim % 10 == 2 and 7 * 6 % 10 == 2
    assert 3850 * 26 == 100100
    assert sum(map(int, "3847")) == 22 and 22 % 9 == 4
    assert 26 % 9 == 8 and 4 * 8 == 32 and 32 % 9 == 5
    assert sum(map(int, str(claim))) == 6
    assert digit_root(claim) == 6 != digit_root(3847 * 26) == 5
    # A multiple of 9 escapes: one error in nine, for a uniform error.
    assert sum(1 for e in range(1, 901) if e % 9 == 0) / 900 == 1 / 9
    # A single wrong digit always moves the digit sum by less than 10, so it is caught unless the shift is 9.
    assert 100 % 9 == 1


def test_q22():
    assert 73 * 68 == 4964
    assert all(str(o)[-1] == "4" for o in (4964, 4954, 5064, 4864)) and 3 * 8 == 24
    assert 73 % 9 == 1 and 68 % 9 == 5
    assert sum(map(int, "73")) == 10 and sum(map(int, "68")) == 14
    assert [o % 9 for o in (4964, 4954, 5064, 4864)] == [5, 4, 6, 4]
    assert sum(map(int, "4964")) == 23 and sum(map(int, "4954")) == 22
    assert sum(map(int, "5064")) == 15 and sum(map(int, "4864")) == 22
    assert F(141, 2) ** 2 - F(5, 2) ** 2 == 4964
    assert F(141, 2) ** 2 == F(497025, 100) and F(5, 2) ** 2 == F(625, 100)
    assert min((4964, 4954, 5064, 4864), key=lambda o: abs(o - 4900)) == 4864


def test_q23():
    assert 71 * 88 == 6248 and sorted("6428") == sorted("6248")
    assert 71 % 9 == 8 and 88 % 9 == 7 and 8 * 7 == 56 and 56 % 9 == 2 and 6428 % 9 == 2
    assert sum(map(int, "6428")) == 20
    assert alt_sum(6428) == 8 - 2 + 4 - 6 == 4 and alt_sum(6248) == 8 - 4 + 2 - 6 == 0
    assert 6428 % 11 == 4 and 6248 % 11 == 0 and 88 == 8 * 11
    assert F(428, 8) == F(107, 2) and F(248, 8) == 31
    # Swapping neighbouring digits a, b moves the alternating sum by twice their difference.
    for a in range(10):
        for b in range(10):
            change = 2 * (a - b)
            assert (alt_sum(int(f"1{a}{b}")) - alt_sum(int(f"1{b}{a}"))) in (change, -change)
            if a != b:
                assert change % 11 != 0


def test_q24():
    assert F(12, 10) * F(85, 100) == F(102, 100) == F(85, 100) * F(12, 10)
    a, b = F(20, 100), -F(15, 100)
    assert a + b + a * b == F(2, 100) and a + b == F(5, 100) and a * b == -F(3, 100)
    assert F(11, 10) * F(9, 10) == F(99, 100)
    assert F(3, 2) * F(1, 2) == F(3, 4)
    # From 100: the rise adds 20 and the fall removes 18, less than the rise put in, so the net is +2.
    assert 100 * F(20, 100) == 20 and 120 * F(15, 100) == 18 and 100 + 20 - 18 == 102


def test_q25():
    x = F(3, 100)
    assert 1 + x + x**2 + x**3 == F(1030927, 1000000)
    assert 1 - x + x**2 - x**3 == F(970873, 1000000)
    assert round(1 / 0.97, 4) == 1.0309 and round(1 / 1.03, 4) == 0.9709
    assert abs(1 / 0.97 - 1.030927) < 2e-6 and abs(1 / 1.03 - 0.970873) < 2e-6
    assert float(x**4) < 1e-6
    assert 1 / F(8, 10) == F(5, 4)
    assert round((1 / 0.97 - 1.03) * 10_000) == 9


def test_q26():
    assert round(1.05**10, 5) == 1.62889
    assert round(1.05**2, 4) == 1.1025 and round(1.1025**2, 4) == 1.2155
    assert round(1.2155 * 1.05, 4) == 1.2763 and round(1.2763**2, 3) == 1.629
    assert round(1 + 2 * 0.1025 + 0.1025**2, 4) == 1.2155
    assert round(0.05 - 0.00125 + 0.00004, 5) == 0.04879 and round(math.log(1.05), 5) == 0.04879
    assert round(math.exp(0.5), 4) == 1.6487 and round(math.exp(-0.0121), 3) == 0.988
    assert round(1.6487 * 0.988, 3) == 1.629
    assert round(math.exp(0.5), 2) == 1.65
    assert round(72 / 5, 1) == 14.4 and round(10 / 14.4, 3) == 0.694 and round(2**0.694, 2) == 1.62
    terms = [math.comb(10, k) * 0.05**k for k in range(5)]
    assert [math.comb(10, k) for k in range(5)] == [1, 10, 45, 120, 210]
    assert round(sum(terms), 4) == 1.6288
    assert round(0.05**4, 8) == 0.00000625


def test_q27():
    exact = F(99, 100) ** 100
    assert round(float(exact), 5) == 0.36603
    assert round(float(math.log(0.99)), 5) == -0.01005
    assert round(math.exp(-1), 4) == 0.3679 and round(0.3679 * 0.995, 3) == 0.366
    assert round(math.exp(-1), 3) == 0.368
    assert round(100 * math.log(1.01), 3) == 0.995 and round(math.e * 0.995, 3) in (2.705, 2.704)
    assert round(float(F(101, 100) ** 100), 5) == 2.70481
    assert round(1 / 1.01**100, 5) == 0.36971
    assert round(100 * (1 - float(exact)), 1) == 63.4
    rng = np.random.default_rng(27)
    sims = (rng.random((200_000, 100)) < 0.01).any(axis=1).mean()
    assert abs(sims - (1 - float(exact))) < 0.005


def test_q28():
    exact = lambda r: math.log(2) / math.log(1 + r / 100)  # noqa: E731
    assert round(exact(1), 2) == 69.66 and round(72 / exact(1) - 1, 3) == 0.034
    assert round(exact(36), 2) == 2.25 and round(1 - 2 / exact(36), 2) == 0.11
    assert round(exact(8) * 8, 2) == 72.05 and round(exact(36) * 36, 1) == 81.2
    # Root of the numerator minus 72, by bisection.
    lo, hi = 1.0, 20.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if exact(mid) * mid < 72:
            lo = mid
        else:
            hi = mid
    assert round(lo, 2) == 7.85
    assert round(100 * math.log(2) / 2 / 100, 2) == 0.35
    assert round((69.3 + 36 / 3) / 36, 2) == 2.26 and 69.3 + 36 / 3 == 81.3
    assert round(69.3 + 1 / 3, 1) == 69.6


def test_q29():
    assert round(252 * 10 / 100, 1) == 25.2
    assert round(0.001 - 0.0000005, 7) == 0.0009995 and round(252 * 0.0009995, 4) == 0.2519
    x = 0.2519
    assert round(1 + x + x**2 / 2 + x**3 / 6, 4) == 1.2863
    assert round(x**4 / 24, 5) == 0.00017
    exact = float(F(1001, 1000) ** 252)
    assert round(exact, 5) == 1.28643 and round(100 * (exact - 1), 1) == 28.6
    down = float(F(999, 1000) ** 252)
    assert round(down, 3) == 0.777 and round(100 * (1 - down), 1) == 22.3
    assert round(math.log(down), 4) == -0.2521
    assert exact * down < 1
    assert round(5 * 0.2519, 2) == 1.26 and round(math.exp(1.26), 1) == 3.5
    assert round(5 * 25.2) == 126


def test_q30():
    exact = float((F(11, 10) * F(9, 10)) ** 50)
    assert round(exact, 3) == 0.605 and round(100 * (1 - exact), 1) == 39.5
    assert round(50 * math.log(0.99), 4) == -0.5025 and round(math.exp(-0.5025), 3) == 0.605
    assert round(math.exp(-0.5), 3) == 0.607
    assert round(0.1**2 / 2, 3) == 0.005 and round(100 * 0.005, 1) == 0.5
    assert round(float(F(96, 100) ** 50), 3) == 0.130 and round(math.exp(-2), 3) == 0.135
    assert round(0.01**2 / 2 * 252 * 100, 2) == 1.26


def test_q31():
    half = math.log(2) / -math.log(0.97)
    dbl = math.log(2) / math.log(1.03)
    assert round(half, 2) == 22.76 and round(dbl, 2) == 23.45
    assert half < dbl < 72 / 3 == 24
    assert round(-math.log(0.97), 4) == 0.0305
    assert round(69.3 / 3, 1) == 23.1
    assert round((69.3 - 3 / 3) / 3, 1) == 22.8 and 69.3 - 1 == 68.3
    assert round(50 / 3, 1) == 16.7
    assert round(half) == 23


def test_q32():
    assert 7**4 == 2401 and 2**5 * 3 * 5**2 == 2400
    log5 = 1 - 0.301
    assert round(log5, 3) == 0.699
    total = 5 * 0.301 + 0.477 + 2 * log5
    assert round(total, 3) == 3.380 and round(total / 4, 3) == 0.845
    assert round(math.log10(7), 4) == 0.8451
    assert round((1 + log5) / 2, 4) == 0.8495
    assert round((0.301 + 0.477 + 3 * 0.301) / 2, 4) == 0.8405
    assert round(0.301 + 0.477, 3) == 0.778 and round(3 * 0.301, 3) == 0.903
    assert 13 * 5 == 65 and 2**6 == 64 and round(6 * 0.301, 3) == 1.806
    assert round(math.log(65 / 64), 4) == 0.0155 and round(0.0155 * 0.434, 4) == 0.0067
    assert round(1.806 + 0.0067 - 0.699, 3) == 1.114 and round(math.log10(13), 3) == 1.114


def test_q33():
    assert len(str(2**100)) == 31 and str(2**100)[0] == "1"
    assert str(2**100).startswith("12676")
    assert round(100 * 0.30103, 3) == 30.103
    assert round(1 - 3 * 0.30103, 4) == 0.0969
    assert round(0.103 - 0.0969, 3) == 0.006
    assert round(10**0.006, 3) == 1.014 and round(1.25 * 1.014, 3) in (1.268, 1.267)
    assert len(str(3**50)) == 24 and str(3**50)[:3] == "717"
    assert round(50 * 0.47712, 3) == 23.856
    assert len(str(2**64)) == 20


def test_q34():
    assert round(2.303 - 3 * 0.693, 3) == 0.224
    assert F(13, 10) / F(125, 100) == F(26, 25)
    assert round(0.04 - 0.0008, 4) == 0.0392
    assert round(0.224 + 0.0392, 3) == 0.263
    assert round(math.log(1.3), 5) == 0.26236
    assert round(math.log(10) - 3 * math.log(2) + math.log(1.04), 3) == 0.262
    assert round(0.3 - 0.045, 3) == 0.255 and round(0.3 - 0.045 + 0.009, 3) == 0.264
    assert 0.3**2 / 2 == 0.045 and round(0.3**3 / 3, 3) == 0.009
    assert 3**4 == 81 and 2**3 * 10 == 80
    assert round(3 * 0.693 + 2.303, 3) == 4.382 and round(math.log(81 / 80), 4) == 0.0124
    assert round((4.382 + 0.0124) / 4, 3) == 1.099


def test_q35():
    assert round(2**0.1, 3) == 1.072 and round(3**0.2, 3) == 1.246
    x = 0.0693
    assert round(1 + x + x**2 / 2 + x**3 / 6, 4) == 1.0718
    y = 1.099 / 5
    assert round(y, 4) == 0.2198
    assert round(y**2 / 2, 4) == 0.0242 and round(y**3 / 6, 4) == 0.0018 and round(y**4 / 24, 4) == 0.0001
    assert round(1 + 0.2198 + 0.0242 + 0.0018 + 0.0001, 3) == 1.246
    assert round(1 + y + y**2 / 2 + y**3 / 6 + y**4 / 24, 3) == 1.246
    assert round(3**0.2, 4) == 1.2457
    assert round(100 * (2**0.1 - 1), 2) == 7.18 and 72 / 10 == 7.2
    assert round(1.1**10, 2) == 2.59
    assert round(math.log(1.12), 4) == 0.1133 and round(0.1133 / 12, 5) == 0.00944
    assert round(100 * (1.12 ** (1 / 12) - 1), 3) == 0.949


def test_q36():
    exact = 47 * 62 * 81 * 19
    assert exact == 4484646 and 50 * 60 * 80 * 20 == 4800000
    assert round(100 * (50 / 47 - 1), 1) == 6.4 and round(100 * (20 / 19 - 1), 1) == 5.3
    assert round(100 * (1 - 60 / 62), 1) == 3.2 and round(100 * (1 - 80 / 81), 1) == 1.2
    assert round(6.4 + 5.3 - 3.2 - 1.2, 1) == 7.3
    est = 4.8e6 / 1.073
    assert round(est / 1e6, 2) == 4.47 and abs(est / exact - 1) < 0.003
    assert 0.06 < 4.8e6 / exact - 1 < 0.08


def test_q37():
    p10, p12 = F(math.comb(20, 10), 2**20), F(math.comb(20, 12), 2**20)
    assert round(float(p10), 4) == 0.1762 and round(float(p12), 4) == 0.1201
    assert round(math.sqrt(5), 2) == 2.24 and round(0.4 / 2.24, 2) == 0.18
    assert round(math.exp(-4 / 10), 2) == 0.67 and round(0.18 * 0.67, 2) == 0.12
    assert round(0.4 / 5, 2) == 0.08 and round(math.comb(100, 50) / 2**100, 4) == 0.0796
    rng = np.random.default_rng(37)
    heads = rng.binomial(20, 0.5, 1_000_000)
    assert abs((heads == 10).mean() - float(p10)) < 0.002
    assert abs((heads == 12).mean() - float(p12)) < 0.002


def test_q38():
    c1, c2 = math.comb(50, 25), math.comb(100, 30)
    assert f"{c1:.3e}" == "1.264e+14" and f"{c2:.3e}" == "2.937e+25"
    assert f"{c1:.1e}" == "1.3e+14" and f"{c2:.1e}" == "2.9e+25"
    assert round(1.024**5, 3) == 1.126 and round(2**50 / 1e15, 3) == 1.126
    assert round(math.sqrt(25 * math.pi), 2) == 8.86
    assert round(1.126e15 / 8.86 / 1e14, 2) == 1.27
    h = -0.3 * math.log2(0.3) - 0.7 * math.log2(0.7)
    assert round(h, 3) == 0.881
    assert f"{2**88.1:.1e}" == "3.3e+26"
    assert round(math.sqrt(2 * math.pi * 21), 1) == 11.5
    assert f"{3.3e26 / 11.5:.1e}" == "2.9e+25"
    assert round(50**25 / math.factorial(25) / c1, -2) == 1500
    assert math.comb(52, 26) == c1 * 52 * 51 // (26 * 26)
    assert round(52 * 51 / (26 * 26), 2) == 3.92 and f"{math.comb(52, 26):.2e}" == "4.96e+14"


def test_q39():
    exact = math.lgamma(53) / math.log(2)
    assert round(exact, 2) == 225.58
    assert round(math.log2(52), 2) == 5.70 and F(52, 32) == F(13, 8) and round(math.log2(1.625), 2) == 0.70
    assert round(52 * 5.70, 1) == 296.4 and round(52 / 0.693, 1) == 75.0
    assert round(2 * math.pi * 52) == 327 and round(0.5 * math.log2(327), 1) == 4.2
    assert round(296.4 - 75.0 + 4.2, 1) == 225.6
    assert round(225.6 * 0.301, 1) == 67.9
    assert len(str(math.factorial(52))) == 68 and str(math.factorial(52))[0] == "8"
    assert 52 * 6 == 312 and 312 - 226 > 80


def test_q40():
    power = F(107, 100) ** 30
    factor = (1 - 1 / power) / F(7, 100)
    assert round(float(factor), 2) == 12.41 and round(float(factor), 1) == 12.4
    assert round(float(power), 2) == 7.61 and round(1.07**10, 3) == 1.967
    assert round(1.967**3, 1) == 7.6 and round(1 / 7.61, 3) == 0.131
    assert round((1 - 0.131) / 0.07, 1) == 12.4
    bond = 5 * factor + 100 / power
    assert round(float(bond), 1) == 75.2 and round(5 * 12.41, 2) == 62.05 and round(100 / 7.61, 2) == 13.14
    assert round(30 / 1.07**15, 1) == 10.9
    assert round(100 / float(factor), 2) == 8.06
    assert round(1 / 0.07, 2) == 14.29 and round(1 - 1 / 7.61, 2) == 0.87
    assert sum(1 / 1.07**k for k in range(1, 31)) > 30 / 1.07**15
