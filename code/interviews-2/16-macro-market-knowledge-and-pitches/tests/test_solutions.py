"""Macro, Market Knowledge and Pitches. The arithmetic behind each reading, with exact checks and limits."""
from math import sqrt

NONNUMERIC = {
    3: "A chain of channels from a surprise to each asset; the answer states the directions first and how to build your own.",
    6: "How to prepare market levels and what to say when you do not know; carries no market level on purpose.",
    15: "Channels of central bank bond buying; the answer states the two channels first, with why they are hard to measure.",
    17: "A pitch structure; the answer gives the recommended order and how to build your own with a placeholder company.",
    22: "A regime map offered with its limits; the table is the answer and it is a framing, not a measured fact.",
}


def test_q1():
    assert 7 * 1 == 7
    v = lambda r, g: 1 / (r - g)  # noqa: E731
    assert round(v(0.09, 0.04) / v(0.08, 0.04) - 1, 2) == -0.2
    assert round(v(0.09, 0.045) / v(0.08, 0.04) - 1, 2) == -0.11
    # If growth rises as much as the rate, the price does not change.
    assert abs(v(0.09, 0.05) / v(0.08, 0.04) - 1) < 1e-12


def test_q2():
    assert round(4.2 - 1.7, 6) == 2.5


def test_q4():
    assert round((4.33 - 4.20) / 0.25, 2) == 0.52
    # Probability-weighted rate reprices the future.
    assert abs(0.52 * (4.33 - 0.25) + 0.48 * 4.33 - 4.20) < 1e-9


def test_q5():
    assert round(0.8 * -0.10 + 0.2 * 0, 4) == -0.08

    # Revenue of 100 (80 in euros, 20 in dollars), costs of 80, split by the share of them in euros.
    def profit_change(eur_share):
        rev = 80 * 0.9 + 20
        cost = 80 * eur_share * 0.9 + 80 * (1 - eur_share)
        return (rev - cost) / 20 - 1

    assert round(profit_change(0.8), 4) == -0.08  # the same share as sales
    assert abs(profit_change(1.0)) < 1e-12  # all in euros: unchanged, so less than 8%
    assert round(profit_change(0.0), 4) == -0.40  # all in dollars: much harder


def test_q7():
    per_gal = 10 / 42
    assert round(per_gal, 3) == 0.238 and round(per_gal * 1000) == 238
    assert round(per_gal * 1000 / 1000, 2) == 0.24 and round(per_gal * 500) == 119


def test_q8():
    f = (1.04**10 / 1.045**2) ** (1 / 8) - 1
    assert round(f * 100, 3) == 3.875 and (10 * 4.0 - 2 * 4.5) / 8 == 3.875
    # A flat curve gives the same forward.
    assert abs((1.04**10 / 1.04**2) ** (1 / 8) - 1.04) < 1e-12


def test_q9():
    assert 5 - 0.5 * 20 == -5


def test_q10():
    r = lambda p, y: 2 + p + 0.5 * (p - 2) + 0.5 * y  # noqa: E731
    assert r(3, 1) == 6 and r(4, 1) == 7.5 and r(4, 1) - r(3, 1) == 1.5
    assert r(2, 0) == 4


def test_q11():
    v = lambda rho: 0.36 * 0.0256 + 0.16 * 0.0049 + 2 * 0.24 * rho * 0.16 * 0.07  # noqa: E731
    assert round(sqrt(v(-0.3)), 3) == 0.092 and round(sqrt(v(0.3)), 3) == 0.108
    assert round(v(0), 4) == 0.01 and round(2 * 0.24 * 0.16 * 0.07, 5) == 0.00538


def test_q12():
    assert 150000 / 30000 == 5 and 5 * 10000 == 50000


def test_q13():
    assert round(0.6 * 25) == 15 and round(0.2 * 25) == 5
    assert round((15 - 5) * 10000) == 100000
    # A parallel fall leaves the steepener flat.
    assert (10 - 10) * 10000 == 0


def test_q14():
    x = 1.005 / 1.045
    assert round(x, 4) == 0.9617 and round(x - 1, 4) == -0.0383
    assert round(0.04 / 0.10, 1) == 0.4
    assert round(1.045 * 0.90 / 1.005 - 1, 2) == -0.06


def test_q16():
    assert round(1.05 * 18 / 20, 3) == 0.945


def test_q18():
    bull, base, bear = 3.6 * 18, 3.3 * 16, 2.7 * 12
    assert round(bull, 2) == 64.8 and round(base, 2) == 52.8 and round(bear, 2) == 32.4
    r = [round(x / 50 - 1, 3) for x in (bull, base, bear)]
    assert r == [0.296, 0.056, -0.352]
    ev = 0.5 * r[0] + 0.3 * r[1] + 0.2 * r[2]
    assert round(ev, 4) == 0.0944
    assert round(r[0] / -r[2], 2) == 0.84 and round(r[0] / 0.12, 2) == 2.47
    size = 0.01 / 0.12
    assert round(size, 3) == 0.083
    assert round(size * 0.352, 3) == 0.029 and round(size * 0.352 / 0.01) == 3


def test_q19():
    a, b = 10000 / (1.9e-4), 10000 / (8e-4)
    assert round(a / 1e6, 1) == 52.6 and round(b / 1e6, 1) == 12.5
    assert 25 * 10000 == 250_000
    carry = round(a * (0.04 - 0.041)) + round(b * (0.041 - 0.042))
    assert round(a * 0.001, -2) == 52600 and round(b * 0.001, -2) == 12500
    assert round(carry, -3) == -65000
    assert round(65000 / 12, -2) == 5400 and round(65000 / 4 / 10000, 1) == 1.6
    assert round(6 * 10000 * 2.326, -2) == 139_600
    # DV01 neutrality: a parallel move has no effect, by construction.
    assert abs(a * 1.9e-4 - b * 8e-4) < 1e-9


def test_q20():
    assert 4 - 8 == -4
    assert round(1.7 + 3, 1) == 4.7 and round(1.7 + 3 - 8, 1) == -3.3
    # If yields do not change at all, each earns its carry.
    assert 4 - 0 == 4


def test_q21():
    assert round(-7.5 * 0.5, 2) == -3.75 and round(-8 * 0.6, 2) == -4.8
    assert 60 - 10 == 50


def test_q23():
    un = 1.10 * 0.95 - 1
    assert round(un, 3) == 0.045
    f = 1.045 / 1.025
    assert round(f, 4) == 1.0195
    h = f - 0.95
    assert round(h, 4) == 0.0695 and round(un + h, 4) == 0.1145
    # If the euro holds, the hedge earns the carry alone, and with equal rates it earns nothing.
    assert round(f - 1, 3) == 0.02 and abs(1.03 / 1.03 - 1) < 1e-12


def test_q24():
    r = 2 * 4.25 - 4.33
    assert round(r, 2) == 4.17 and round((4.33 - r) / 0.25, 2) == 0.64
    assert round((r - 4.10) / 0.25, 2) == 0.28
    assert round(4.33 - 4.10, 2) == 0.23
    assert round((4.33 - 4.25) / 0.25, 2) == 0.32


def test_q25():
    p = [0.25, 0.5, 0.25]
    eq = [1.0, 0.3, -1.5]
    dy = [-8, 0, 10]
    pnl = [e - 0.05 * d for e, d in zip(eq, dy, strict=True)]
    assert [round(x, 6) for x in pnl] == [1.4, 0.3, -2.0]
    mean = sum(a * b for a, b in zip(p, pnl, strict=True))
    assert abs(mean) < 1e-12
    var = sum(a * b * b for a, b in zip(p, pnl, strict=True))
    assert round(var, 3) == 1.535 and round(sqrt(var), 2) == 1.24
    am = sum(a * abs(b) for a, b in zip(p, eq, strict=True))
    assert round(am, 3) == 0.775 and round(1 - am / 1, 3) == 0.225
    assert round(0.05 * 10 / 2.0, 2) == 0.25
    assert round(-1.5 * 0.7 - 0.5, 2) == -1.55 and round(-1.5 * 0.7, 2) == -1.05
