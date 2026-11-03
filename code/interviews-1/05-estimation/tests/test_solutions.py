"""Every number printed in the answers of "Estimation": the sum, a second route, and a limit case where one exists."""
import math

import numpy as np
from scipy import stats

NONNUMERIC = {}


def near(a, b, tol=0.01):
    return abs(a - b) <= tol * abs(b)


def test_q1():
    year = 365.25 * 86400
    assert year == 31_557_600
    assert near(year, math.pi * 1e7, 0.005)
    trading = 252 * 6.5 * 3600
    assert trading == 5_896_800
    assert near(trading / year, 0.187, 0.01)
    assert 252 * 390 == 98_280


def test_q2():
    volume = 50 * 25 * 2
    assert volume == 2500
    rate = 20 * 60 / 1000  # m3 per hour at 20 litres a minute
    assert near(volume / rate / 24, 87, 0.01)
    assert near(volume / (40 * 60 / 1000) / 24, 43, 0.02)
    assert near(volume / (10 * 60 / 1000) / 24, 174, 0.01)
    # Second route: a 10-litre bucket in 30 seconds is the same 20 litres a minute.
    assert 10 / 0.5 == 20


def test_q3():
    assert near(2**32 / 1e6 / 60, 71.6, 0.001)
    assert near(2**64 / 1e6 / (365.25 * 86400), 584_542, 0.001)
    day = 6.5 * 3600 * 1e6
    assert day == 2.34e10
    assert 2**34 < day < 2**35


def test_q4():
    assert near(5 * math.sqrt(252), 79.4, 0.001)
    assert near(20 / math.sqrt(252), 1.26, 0.002)
    assert near((20 / (5 * math.sqrt(252))) ** 2, 0.063, 0.01)
    # Follow-up: 248 ordinary days at 1% and 4 earnings days at 5%.
    assert near(math.sqrt(248 + 4 * 25), 18.7, 0.003)
    # If nothing changes (all days 1.26%) the annual figure comes back to 20.
    assert near(math.sqrt(252 * (20 / math.sqrt(252)) ** 2), 20, 1e-9)


def test_q5():
    fibre, air = 200_000, 300_000
    assert 1200 / fibre * 1000 == 6
    assert 1200 / air * 1000 == 4
    assert fibre * 1e3 * 1e-9 * 100 == 20  # centimetres per nanosecond
    assert round(air * 1e3 * 1e-9 * 100) == 30
    # A few metres of cable at 20 cm per nanosecond: two metres cost 10 ns, four metres 20 ns.
    assert 200 / 20 == 10 and 400 / 20 == 20


def test_q6():
    kwh = 0.5 * 8760
    assert kwh == 4380
    assert near(kwh * 0.10, 438, 1e-9)
    assert near(kwh * 0.10 * 1.5, 657, 1e-9)
    assert 10_000 / 4 == 2500
    assert near(657 / (2500 + 657), 0.208, 0.005)
    # With free electricity the share falls to zero.
    assert 0 / (2500 + 0) == 0


def test_q7():
    volume = 200_000 * 1000 / 19_300  # kg over kg/m3
    assert near(volume, 10_363, 0.001)
    assert near(volume ** (1 / 3), 21.8, 0.002)
    ounces = 200_000 * 1e6 / 31.1
    assert near(ounces, 6.43e9, 0.001)
    assert near(ounces * 3000, 19.3e12, 0.001)
    assert near(200_000 * 1e6 / 8e9, 25, 1e-9)


def test_q8():
    assert 1e6 * 6 / 2500 == 2400
    assert 1e6 * 4 / 4000 == 1000
    assert near(1e6 * 10 / 1500, 6667, 0.001)
    assert near(math.sqrt(1000 * 6667), 2582, 0.001)
    assert near(1e6 / 2400, 417, 0.001)


def test_q9():
    bus = 12 * 2.5 * 2 * 0.8
    assert bus == 48
    ball = 4 / 3 * math.pi * 2.15**3
    assert near(ball, 41.6, 0.001)
    packed = bus * 0.6 / (ball * 1e-6)
    assert near(packed, 692_000, 0.002)
    cubic = bus / (4.3**3 * 1e-6)
    assert near(cubic, 604_000, 0.002)
    assert near(math.pi / 6, 0.52, 0.01)  # the packing the cubic route implies
    # The two routes are the same formula: dividing by the packing fractions recovers the ratio.
    assert near(packed / cubic, 0.6 / (math.pi / 6), 1e-9)
    # Sphere packing cannot exceed the densest packing, which caps the answer.
    assert bus * 0.74 / (ball * 1e-6) < 1e6


def test_q10():
    a = 8e9 * 0.5 * 2.5 / 8760
    assert near(a, 1.14e6, 0.005)
    b = 25_000 * 10 / 24 * 130
    assert near(b, 1.35e6, 0.005)
    assert near(25_000 * 10 / 24, 10_400, 0.002)
    assert near(b / a, 1.19, 0.01)
    assert near(8e9 / 1.2e6, 6667, 0.01)


def test_q11():
    fills = 200e6 / 10
    assert fills == 20e6
    assert fills / 200 == 100_000
    assert 300e6 / 100_000 == 3000
    assert 200 * 40 * 0.05 == 400
    assert 365 * 400 == 146_000
    # The low and high ends: 400 and 100 fills a day.
    assert fills / 400 == 50_000 and fills / 100 == 200_000


def test_q12():
    sigma = math.log(2) / stats.norm.ppf(0.95)
    assert near(sigma, 0.4214, 0.001)
    assert near(math.exp(sigma * math.sqrt(4) * stats.norm.ppf(0.95)), 4, 1e-9)
    assert near(math.exp(sigma * 3 * stats.norm.ppf(0.95)), 8, 1e-9)
    assert near(math.exp((2 * sigma) ** 2 / 2), 1.43, 0.005)
    rng = np.random.default_rng(12)
    z = rng.normal(0, sigma, (400_000, 4)).sum(axis=1)
    assert abs(np.mean(np.abs(z) < math.log(4)) - 0.90) < 0.002
    # A factor of 16 is exactly twice the 1.645 point, 3.29 standard deviations: about 99.9%.
    assert near(math.log(16) / (2 * sigma), 2 * stats.norm.ppf(0.95), 1e-9)
    assert near(2 * stats.norm.cdf(2 * stats.norm.ppf(0.95)) - 1, 0.999, 0.0005)
    assert abs(np.mean(np.abs(z) < math.log(16)) - 0.999) < 0.0005
    # One factor is the limit case: the interval stays a factor of two.
    assert abs(np.mean(np.abs(rng.normal(0, sigma, 400_000)) < math.log(2)) - 0.90) < 0.002
    # Perfectly correlated factors: the same draw four times gives sixteen.
    same = 4 * rng.normal(0, sigma, 400_000)
    assert abs(np.mean(np.abs(same) < math.log(16)) - 0.90) < 0.002


def test_q13():
    value = 60e12 * 2 / 252
    assert near(value, 476e9, 0.001)
    trades = value / 20_000
    assert near(trades, 23.8e6, 0.001)
    per_s = trades / (6.5 * 3600)
    assert near(per_s, 1017, 0.001)
    msgs = per_s * 30
    assert near(msgs, 30_500, 0.001)
    peak = msgs * 20
    assert near(peak, 610_000, 0.001)
    assert near(peak * 40, 24.4e6, 0.001)
    assert near(peak * 40 * 8, 195e6, 0.002)


def test_q14():
    shares = 10e9 * 0.05
    assert shares == 500e6
    low, mid, high = [shares * c / 100 * 252 for c in (0.05, 0.1, 0.2)]
    assert near(mid, 126e6, 1e-9)
    assert near(low, 63e6, 1e-9) and near(high, 252e6, 1e-9)
    assert near(0.1 / 0.5, 0.2, 1e-9)
    # With nothing kept, nothing is earned.
    assert shares * 0 / 100 * 252 == 0


def test_q15():
    msgs = 5000 * 10 * 6.5 * 3600
    assert msgs == 1.17e9
    day = msgs * 40
    assert near(day, 46.8e9, 1e-9)
    year = day * 252
    assert near(year, 11.8e12, 0.001)
    assert near(year / 5, 2.36e12, 0.001)
    assert near(day / 1e9, 47, 0.01)
    # One stock's average share of the day's read: about 9 ms. A busy one holds many times that share.
    assert near(day / 1e9 / 5000 * 1000, 9.36, 0.001)
    busy_share = 0.8 / 300  # for instance, 300 names with 80% of the updates
    assert busy_share > 10 / 5000 and busy_share * day / 1e9 < day / 1e9 / 100


def test_q16():
    bars = 5000 * 252 * 20 * 390
    assert bars == 9_828_000_000
    assert near(bars * 40, 393e9, 0.001)
    assert near(bars * 40 / 1e9, 393, 0.001)  # seconds of disk
    assert near(393 / 60, 6.55, 0.001)
    assert near(bars * 1e-6, 9828, 1e-9)
    assert near(bars * 1e-6 / 3600, 2.73, 0.001)
    assert near(bars * 1e-6 / 16, 614, 0.001)
    assert bars * 1e-6 / 16 > bars * 40 / 1e9  # cores still bind at 16
    assert near(bars * 1e-6 / (bars * 40 / 1e9), 25, 1e-9)  # the crossover in cores
    assert round(bars * 1e-6 / 3600, 1) == 2.7


def test_q17():
    half = 1e-4
    daily = 500e9 * half
    assert daily == 50e6
    assert near(daily * 252, 12.6e9, 1e-9)
    assert near(daily * 252 / 60e12 * 1e4, 2.1, 1e-9)
    assert near(500e9 * 2e-4 * 252, 25.2e9, 1e-9)  # the double counting
    assert 500e9 * 0 * 252 == 0


def test_q18():
    assert near(1e6 / 100e6, 0.01, 1e-9)
    assert near(1e6 / 10e6, 0.10, 1e-9)
    assert 0.10 / 0.02 == 5


def test_q19():
    mass = 1e5 / 10 * 4 * math.pi * (6.4e6) ** 2
    assert near(4 * math.pi * (6.4e6) ** 2, 5.15e14, 0.001)
    assert near(mass, 5.15e18, 0.001)
    moles = mass * 1000 / 29
    assert near(moles, 1.77e20, 0.003)
    atmosphere = moles * 6e23
    assert near(atmosphere, 1.06e44, 0.005)
    breath = 0.5 / 24 * 6e23
    assert near(0.5 / 24, 0.0208, 0.002)
    assert near(breath, 1.25e22, 0.001)
    expected = breath * breath / atmosphere
    assert near(expected, 1.46, 0.01)
    assert near(1 - math.exp(-expected), 0.77, 0.01)
    # A simulation of the draw: each of your molecules is Caesar's with the atmosphere's share.
    rng = np.random.default_rng(19)
    # The huge numbers cannot be drawn directly, and only n * n / N matters, so draw a scaled copy with the same ratio.
    small_n = 100_000
    small_atmosphere = small_n**2 / expected
    hits = rng.binomial(small_n, small_n / small_atmosphere, 400_000)
    assert abs(hits.mean() - expected) < 0.01
    assert abs((hits >= 1).mean() - (1 - math.exp(-expected))) < 0.003
    # Double the breath and the expected count goes up four times: the count is quadratic.
    assert near((2 * breath) ** 2 / atmosphere / expected, 4, 1e-9)


def test_q20():
    log10 = math.lgamma(53) / math.log(10)
    assert near(log10, 67.9, 0.001)
    stirling = 52 * math.log(52) - 52 + 0.5 * math.log(2 * math.pi * 52)
    assert near(52 * math.log(52), 205.46, 0.001)
    assert near(0.5 * math.log(2 * math.pi * 52), 2.89, 0.002)
    assert near(stirling, 156.36, 0.001)
    assert near(stirling / math.log(10), 67.9, 0.001)
    assert near((52 * math.log(52) - 52) / math.log(10), 66.6, 0.002)
    orderings = math.factorial(52)
    assert near(orderings, 8.07e67, 0.001)
    atoms = 6e24 * 1000 / 30 * 6e23
    assert near(atoms, 1.2e50, 1e-9)
    assert near(orderings / atoms, 6.7e17, 0.01)
    seen = 1e9 * 4.4e17
    assert near(seen, 4.4e26, 1e-9)
    assert near(orderings / seen, 1.8e41, 0.02)
    match = math.sqrt(2 * math.log(2) * orderings)
    assert near(match, 1.06e34, 0.005)
    # The birthday formula must hold where it can be checked by exact product: 23 for 365.
    p = 1.0
    for k in range(23):
        p *= (365 - k) / 365
    assert p < 0.5 and near(math.sqrt(2 * math.log(2) * 365), 22.5, 0.01)


def test_q21():
    tail = stats.binom.cdf(5, 10, 0.9)
    assert near(tail, 0.00163, 0.01)
    factor = stats.norm.ppf(0.95) / stats.norm.ppf(0.75)
    assert near(factor, 2.44, 0.002)
    assert near(math.exp(math.log(3) * factor), 14.6, 0.005)
    low = stats.beta.ppf(0.025, 5, 6)
    high = stats.beta.ppf(0.975, 6, 5)
    assert near(low, 0.19, 0.02) and near(high, 0.81, 0.01)
    rng = np.random.default_rng(21)
    hits = rng.binomial(10, 0.9, 2_000_000)
    assert abs((hits <= 5).mean() - tail) < 0.0002
    # An interval of width z = 1.645 sigma_assumed against a true sigma 2.44 times larger covers half.
    z = rng.normal(0, factor, 1_000_000)
    assert abs(np.mean(np.abs(z) < stats.norm.ppf(0.95)) - 0.5) < 0.002
    # If the widening factor were one, coverage would be the labelled 90%.
    z = rng.normal(0, 1, 1_000_000)
    assert abs(np.mean(np.abs(z) < stats.norm.ppf(0.95)) - 0.9) < 0.002


def test_q22():
    days = 100 * 252
    assert days == 25_200
    z = stats.norm.isf(1 / (2 * days))
    assert near(z, 4.11, 0.005)
    t3 = stats.t.isf(1 / (2 * days), 3) * math.sqrt(1 / 3)
    assert near(t3, 22, 0.05)
    assert 1e-90 < stats.norm.cdf(-20) < 1e-88
    assert near(1 / stats.norm.cdf(-20) / 252, 1.4e86, 0.05)
    rng = np.random.default_rng(22)
    normal = np.abs(rng.normal(0, 1, (400, days))).max(axis=1)
    assert 3.9 < np.median(normal) < 4.5
    fat = np.abs(rng.standard_t(3, (400, days)) * math.sqrt(1 / 3)).max(axis=1)
    assert 15 < np.median(fat) < 35
    # As degrees of freedom grow the t answer falls back to the normal one.
    big = stats.t.isf(1 / (2 * days), 1000) * math.sqrt(998 / 1000)
    assert abs(big - z) < 0.1
    # The median of the maximum: tail ln 2 / 25,200, a little above both figures.
    tail = 1 - 0.5 ** (1 / days)
    assert near(tail, math.log(2) / days, 1e-3)
    assert round(stats.norm.isf(tail / 2), 1) == 4.2
    assert round(stats.t.isf(tail / 2, 3) * math.sqrt(1 / 3)) == 25
    assert abs(np.median(normal) - stats.norm.isf(tail / 2)) < 0.05
    assert abs(np.median(fat) / (stats.t.isf(tail / 2, 3) * math.sqrt(1 / 3)) - 1) < 0.12


def test_q23():
    daily = 1000 * 50e6 * 0.05
    assert daily == 2.5e9
    book = daily * 5 / 2
    assert book == 6.25e9
    assert near(daily * 252, 630e9, 1e-9)
    profit = daily * 252 * 5e-4
    assert near(profit, 315e6, 1e-9)
    assert near(profit / book, 0.0504, 1e-9)
    assert near(daily * 5, 12.5e9, 1e-9)
    # Simulate the schedule: each day 1/5 of the book is closed and a new 1/5 opened.
    lots = [book / 5] * 5
    traded = []
    for _ in range(50):
        closed = lots.pop(0)
        lots.append(book / 5)
        traded.append(closed + book / 5)
        assert near(sum(lots), book, 1e-9)
    assert near(np.mean(traded), daily, 1e-9)
    # A holding period of one day: closes and opens the whole book, so trades twice the book.
    assert near(2 * book / 1, 2 * book, 1e-9)


def test_q24():
    s, lam = 0.8, 1.0  # microseconds, per microsecond
    rho = s * lam
    wait = rho * s / (2 * (1 - rho))
    assert near(wait, 1.6, 1e-9)
    assert near(rho * s / (1 - rho), 3.2, 1e-9)
    assert near(wait + s, 2.4, 1e-9)
    assert 0.9 * s / (2 * 0.1) > 2 * wait  # at 90% load the wait more than doubles
    assert near(0.5 / 1.25, 0.4, 1e-9)
    # Lindley recursion, Poisson arrivals, fixed service.
    rng = np.random.default_rng(24)
    gaps = rng.exponential(1 / lam, 2_000_000)
    w, total = 0.0, 0.0
    for g in gaps:
        w = max(0.0, w + s - g)
        total += w
    assert abs(total / len(gaps) - wait) < 0.03
    # With a very light load there is no queue.
    assert (1e-6 * s * s) / (2 * (1 - 1e-6 * s)) < 1e-5
    # The burst, simulated message by message at steady spacing.
    capacity = 1.25
    backlog = (1.5 - capacity) * 1000
    assert near(backlog, 250, 1e-9)
    assert near(backlog * s, 200, 1e-9)
    drain = backlog / (capacity - 0.5)
    assert near(drain, 333, 0.002)
    finish, end = 0.0, None
    arrivals = [i / 1.5 for i in range(1500)]
    arrivals += [1000 + i / 0.5 for i in range(1000)]
    queue_at_end = None
    for a in arrivals:
        if a >= 1000 and queue_at_end is None:
            queue_at_end = (finish - 1000) / s
        finish = max(finish, a) + s
        if a >= 1000 and finish - a <= s + 1e-9 and end is None:
            end = a
    assert abs(queue_at_end - 250) < 2
    assert abs(end - 1000 - drain) < 3


def test_q25():
    sigma, volume = 0.015, 500e9
    traded = 2 * 20e9
    q = traded / volume
    assert near(q, 0.08, 1e-9)
    cost = sigma * math.sqrt(q)
    assert near(cost * 1e4, 42.4, 0.001)
    target = 0.30 * 20e9
    assert target == 6e9
    needed = target / 252 / traded
    assert near(needed * 1e4, 5.95, 0.001)
    assert near((needed + cost) * 1e4, 48.4, 0.001)
    a = 10e-4
    assert near((a - cost) * traded, -130e6, 0.01)
    star = (2 * a / (3 * sigma)) ** 2
    assert near(star, 0.001975, 0.001)
    assert near(star * volume, 988e6, 0.001)
    assert near(star * volume / 2, 494e6, 0.001)
    net = a - sigma * math.sqrt(star)
    assert near(net * 1e4, 3.33, 0.002)
    assert near(net * star * volume, 329e3, 0.002)
    assert near(net * star * volume * 252, 83e6, 0.005)
    assert near(net * star * volume * 252 / (star * volume / 2), 0.168, 0.002)
    # Second route: search the profit curve by brute force.
    grid = np.linspace(1e-5, 0.02, 200_000)
    profit = grid * volume * (a - sigma * np.sqrt(grid))
    assert near(grid[profit.argmax()], star, 0.001)
    # Limit cases: no signal, no profit at any size; a small enough book keeps nearly all of the 10 bp.
    assert (grid * volume * (0 - sigma * np.sqrt(grid))).max() < 0
    assert near(a - sigma * math.sqrt(1e-9), a, 0.001)
    # At the optimum, cost is two thirds of the signal.
    assert near(sigma * math.sqrt(star) / a, 2 / 3, 1e-9)
