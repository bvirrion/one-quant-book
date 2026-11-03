"""Every rule and number printed in "Sequences, Patterns and Aptitude": the rule rebuilds each term, and rivals fail."""
import itertools
import math
import pathlib
import sys
from fractions import Fraction as F

import numpy as np
import sympy as sp

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

from iv_sequences import (  # noqa: E402
    constant,
    differences,
    digit_product,
    digit_sum,
    fits_simple_rule,
    poly_next,
    ratios,
)

NONNUMERIC = {}


def position(letter):
    return ord(letter) - ord("A") + 1


def word_sum(word):
    return sum(position(c) for c in word)


def test_q1():
    seq = [3, 6, 18, 72]
    assert ratios(seq) == [2, 3, 4]
    assert 72 * 5 == 360
    d = differences(seq)
    assert d == [3, 12, 54] and ratios(d) == [4, F(9, 2)]
    assert not fits_simple_rule(seq)


def test_q2():
    seq = [3, 5, 9, 15, 23]
    assert differences(seq) == [2, 4, 6, 8]
    assert constant(differences(differences(seq)))
    assert [n * n - n + 3 for n in range(1, 7)] == [*seq, 33]
    assert poly_next(seq) == 33
    assert ratios(seq) == [F(5, 3), F(9, 5), F(5, 3), F(23, 15)]
    assert differences([2, 4, 6, 8]) == [2, 2, 2]
    assert differences([2, 4, 8, 16]) == [2, 4, 8]


def test_q3():
    seq = [1, 4, 27, 256]
    assert [n**n for n in range(1, 6)] == [*seq, 3125]
    assert ratios(seq)[0] == 4 and float(ratios(seq)[1]) == 6.75 and round(float(ratios(seq)[2]), 1) == 9.5
    assert not fits_simple_rule(seq)
    assert [n ** (n - 1) for n in range(1, 7)] == [1, 2, 9, 64, 625, 7776]


def test_q4():
    words = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    assert [w[0] for w in words] == list("OTTFFSSEN")
    assert [position(c) for c in "OTTFFSSE"] == [15, 20, 20, 6, 6, 19, 19, 5]
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    assert [d[0] for d in days] == list("MTWTFSS")


def test_q5():
    tri = [n * (n + 1) // 2 for n in range(1, 8)]
    assert tri == [1, 3, 6, 10, 15, 21, 28]
    assert differences(tri[:5]) == [2, 3, 4, 5]
    assert [position(c) for c in "ACFJOU"] == tri[:6]
    assert 28 > 26 and chr(ord("A") + (28 - 1) % 26) == "B"


def test_q6():
    seq = [1, 20, 2, 17, 4, 14, 8, 11]
    assert seq[0::2] == [1, 2, 4, 8] and constant(ratios(seq[0::2]))
    assert seq[1::2] == [20, 17, 14, 11] and constant(differences(seq[1::2]))
    assert len(seq) == 8 and 8 * 2 == 16 and 11 - 3 == 8
    assert differences(seq)[:3] == [19, -18, 15]
    assert not fits_simple_rule(seq)


def test_q7():
    seq = [3, 6, 4, 8, 6, 12, 10]
    x, out = 3, [3]
    for i in range(8):
        x = x * 2 if i % 2 == 0 else x - 2
        out.append(x)
    assert out == [*seq, 20, 18]
    assert seq[0::2] == [3, 4, 6, 10] and differences(seq[0::2]) == [1, 2, 4]
    assert seq[1::2] == [6, 8, 12] and differences(seq[1::2]) == [2, 4]
    assert 12 + 8 == 20 and 10 + 8 == 18


def test_q8():
    grid = [
        [("white", "circle"), ("grey", "square"), ("black", "triangle")],
        [("grey", "triangle"), ("black", "circle"), ("white", "square")],
        [("black", "square"), ("white", "triangle"), None],
    ]
    colours, shapes = {"white", "grey", "black"}, {"circle", "square", "triangle"}
    fits = []
    for c, s in itertools.product(colours, shapes):
        g = [row[:] for row in grid]
        g[2][2] = (c, s)
        rows = all({x[0] for x in r} == colours and {x[1] for x in r} == shapes for r in g)
        cols = all({g[i][j][0] for i in range(3)} == colours and {g[i][j][1] for i in range(3)} == shapes for j in range(3))
        if rows and cols:
            fits.append((c, s))
    assert fits == [("grey", "circle")]
    # Colours do not shift with the shapes, in the way a copy of row 1 would.
    assert [x[1] for x in grid[1]] == [grid[0][2][1], grid[0][0][1], grid[0][1][1]]
    assert [x[0] for x in grid[1]] != [grid[0][2][0], grid[0][0][0], grid[0][1][0]]


def test_q9():
    # Search all sets on a three-person firm: the premises can hold with the conclusion true or false.
    people = range(3)
    subsets = [set(s) for k in range(4) for s in itertools.combinations(people, k)]
    fail, holds = False, False
    implied_some, implied_none = True, True
    for an, de, tr in itertools.product(subsets, repeat=3):
        if not an or not (an <= de):
            continue
        if de & tr:
            if an & tr:
                holds = True
            else:
                fail = True
        if an & tr and not de & tr:
            implied_some = False
        if not de & tr and an & tr:
            implied_none = False
    assert fail and holds and implied_some and implied_none


def test_q10():
    solutions = []
    for truth in itertools.product((False, True), repeat=5):
        false_count = truth.count(False)
        if all(truth[k - 1] == (false_count == k) for k in range(1, 6)):
            solutions.append(truth)
    assert solutions == [(False, False, False, True, False)]
    for n in range(2, 9):
        sols = []
        for truth in itertools.product((False, True), repeat=n):
            fc = truth.count(False)
            if all(truth[k - 1] == (fc == k) for k in range(1, n + 1)):
                sols.append(truth)
        assert len(sols) == 1 and sols[0][n - 2] and sols[0].count(True) == 1


def test_q11():
    seq = [2, 9, 28, 65]
    assert [n**3 + 1 for n in range(1, 6)] == [*seq, 126]
    d1 = differences(seq)
    d2 = differences(d1)
    assert d1 == [7, 19, 37] and d2 == [12, 18] and differences(d2) == [6]
    assert 18 + 6 == 24 and 37 + 24 == 61 and 65 + 61 == 126
    assert poly_next(seq) == 126
    assert math.factorial(3) == 6
    assert not constant(d1)
    # Summing a constant three times gives a cubic, whatever the three starting values.
    for starts in ((0, 0, 0), (2, 7, 12), (-3, 5, 1)):
        s3 = [6] * 8
        s2 = [starts[0]]
        for v in s3:
            s2.append(s2[-1] + v)
        s1 = [starts[1]]
        for v in s2:
            s1.append(s1[-1] + v)
        s0 = [starts[2]]
        for v in s1:
            s0.append(s0[-1] + v)
        k = sp.symbols("k")
        poly = sp.Poly(sp.interpolate(list(zip(range(1, len(s0) + 1), s0, strict=True)), k), k)
        assert poly.degree() == 3 and poly.LC() == 1


def test_q12():
    assert word_sum("CAT") == 3 + 1 + 20 == 24
    assert word_sum("DOG") == 4 + 15 + 7 == 26
    assert word_sum("FOX") == 6 + 15 + 24 == 45
    assert 3 * 1 * 20 == 60
    reverse = lambda w: sum(27 - position(c) for c in w)  # noqa: E731
    assert reverse("CAT") == 24 + 26 + 7 == 57
    assert word_sum("TAX") == 20 + 1 + 24 == 45


def test_q13():
    assert F(240, F(120, 40) + F(120, 60)) == 48
    assert 2 / (F(1, 40) + F(1, 60)) == 48
    assert F(1000, 40) == 25 and round(1000 / 60, 2) == 16.67
    assert 2000 / (F(1000, 40) + F(1000, 60)) == 48


def test_q14():
    assert F(1, 6) + F(1, 3) - F(1, 4) == F(1, 4)
    assert F(2 + 4 - 3, 12) == F(1, 4)
    assert F(1, 6) + F(1, 3) - F(1, 2) == 0
    assert F(1, 6) + F(1, 3) == F(1, 2)
    assert 6 + 3 - 4 == 5
    # Step the tank forward in small steps: the level reaches 1 at 4 hours.
    level, t, dt = 0.0, 0.0, 1e-4
    while level < 1:
        level += (1 / 6 + 1 / 3 - 1 / 4) * dt
        t += dt
    assert abs(t - 4) < 1e-2


def test_q15():
    total, m, p, neither = 40, 25, 18, 7
    assert m + p == 43 and total - neither == 33 and m + p - (total - neither) == 10
    # Enumerate every overlap that the two totals allow.
    possible = [b for b in range(0, 19) if m + p - b <= total and b <= min(m, p)]
    assert min(possible) == 3 and max(possible) == 18
    assert 25 + 18 - 40 == 3
    assert total - (m + p - 18) == 15


def test_q16():
    rows = {"X": (200, 150, 250, 180), "Y": (400, 320, 500, 395), "Z": (120, 96, 150, 111)}
    points, dollars, growth = {}, {}, {}
    for k, (r1, c1, r2, c2) in rows.items():
        points[k] = 100 * F(r2 - c2, r2) - 100 * F(r1 - c1, r1)
        dollars[k] = (r2 - c2) - (r1 - c1)
        growth[k] = 100 * (F(r2 - c2, r1 - c1) - 1)
    assert points == {"X": 3, "Y": 1, "Z": 6}
    assert dollars == {"X": 20, "Y": 25, "Z": 15}
    assert max(points, key=points.get) == "Z" and max(dollars, key=dollars.get) == "Y"
    assert F(50, 200) == F(25, 100) and F(70, 250) == F(28, 100)
    assert F(80, 400) == F(20, 100) and F(105, 500) == F(21, 100)
    assert F(24, 120) == F(20, 100) and F(39, 150) == F(26, 100)
    assert float(growth["Z"]) == 62.5 and float(growth["X"]) == 40.0 and round(float(growth["Y"])) == 31


def test_q17():
    primes = list(sp.primerange(2, 20))
    prods = [a * b for a, b in zip(primes, primes[1:], strict=False)]
    assert prods == [6, 15, 35, 77, 143, 221, 323]
    assert differences([6, 15, 35, 77, 143]) == [9, 20, 42, 66]
    assert not fits_simple_rule([6, 15, 35, 77, 143])
    assert [p * p for p in primes[:6]] == [4, 9, 25, 49, 121, 169]


def test_q18():
    seq = [19, 29, 40, 44, 52, 59, 73]
    assert all(b == a + digit_sum(a) for a, b in zip(seq, seq[1:], strict=False))
    assert [digit_sum(a) for a in seq[:-1]] == [10, 11, 4, 8, 7, 14]
    assert not fits_simple_rule(seq[:-1])
    # The weak item: both rules fit, and agree until 39.
    other = [12, 15, 21, 24, 30, 33]
    assert all(b == a + digit_sum(a) for a, b in zip(other, other[1:], strict=False))
    assert 33 + digit_sum(33) == 39 and 33 + 6 == 39
    assert 39 + digit_sum(39) == 51 and 39 + 3 == 42


def test_q19():
    seq = [2, 3, 5, 4, 9, 7, 8, 27, 9, 16]
    assert seq[0::3] == [2, 4, 8, 16] and seq[1::3] == [3, 9, 27] and seq[2::3] == [5, 7, 9]
    assert (11 - 1) % 3 == 1 and 27 * 3 == 81
    assert seq[0::2] == [2, 5, 9, 8, 9] and seq[1::2] == [3, 4, 7, 27, 16]
    assert not fits_simple_rule(seq[0::2]) and not fits_simple_rule(seq[1::2])
    assert 11 == 3 * 3 + 2 and 9 + 2 == 11


def base(n, b):
    out = ""
    while n:
        out = str(n % b) + out
        n //= b
    return int(out)


def test_q20():
    seq = [1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 15, 20]
    assert [base(n, 6) for n in range(1, 14)] == [*seq, 21]
    assert differences(seq) == [1, 1, 1, 1, 5, 1, 1, 1, 1, 1, 5]
    assert 2 * 6 + 0 == 12 and seq[11] == 20
    assert base(35, 6) == 55 and base(36, 6) == 100
    assert [base(n, 3) for n in range(1, 10)] == [1, 2, 10, 11, 12, 20, 21, 22, 100]


def test_q21():
    r1 = ({"top", "left"}, {"left", "right"}, {"top", "right"})
    r2 = ({"bottom", "right"}, {"top", "right"}, {"top", "bottom"})
    r3 = ({"top", "left", "bottom"}, {"left", "right"})
    assert r1[0] ^ r1[1] == r1[2] and r2[0] ^ r2[1] == r2[2]
    assert r3[0] ^ r3[1] == {"top", "right", "bottom"}
    assert r1[0] | r1[1] != r1[2] and r1[0] & r1[1] != r1[2]
    assert r1[0] & r1[1] == {"left"} and r1[0] | r1[1] == {"top", "left", "right"}
    assert r3[0] | r3[1] == {"top", "left", "right", "bottom"}
    # As four-bit numbers.
    bits = {"top": 1, "right": 2, "bottom": 4, "left": 8}
    to_int = lambda s: sum(bits[x] for x in s)  # noqa: E731
    assert to_int(r1[0]) ^ to_int(r1[1]) == to_int(r1[2])


def test_q22():
    rows = [(2, 3, 13), (4, 1, 17), (1, 5, 26), (3, 3, 18)]
    assert all(a * a + b * b == c for a, b, c in rows)
    assert 5 * 5 + 2 * 2 == 29
    # No linear rule pa + qb + c fits all four: the system is overdetermined and inconsistent.
    m = np.array([[a, b, 1] for a, b, _ in rows], dtype=float)
    y = np.array([c for _, _, c in rows], dtype=float)
    assert np.linalg.matrix_rank(m) == 3
    sol, *_ = np.linalg.lstsq(m, y, rcond=None)
    assert np.abs(m @ sol - y).max() > 0.5
    # Three rows always fit three free numbers.
    assert abs(np.linalg.det(m[:3])) > 0.5
    # A product plus a constant.
    assert 13 - 2 * 3 == 7 and 17 - 4 * 1 == 13


def test_q23():
    sols = []
    for a, b, c in itertools.product((True, False), repeat=3):
        if a == (not b) and b == (not c) and c == ((not a) and (not b)):
            sols.append((a, b, c))
    assert sols == [(False, True, False)]
    alt = []
    for a, b, c in itertools.product((True, False), repeat=3):
        if a == (not b) and b == (not c) and c == a:
            alt.append((a, b, c))
    assert sorted(alt) == [(False, True, False), (True, False, True)]


def test_q24():
    def ok(p, last=True):
        pos = {x: i for i, x in enumerate(p)}
        cond = pos["C"] < pos["A"] < pos["B"] and pos["D"] == pos["E"] + 1
        return cond and (not last or pos["B"] != 4)

    orders = list(itertools.permutations("ABCDE"))
    assert len(orders) == 120
    chain = [p for p in orders if (lambda q: q["C"] < q["A"] < q["B"])({x: i for i, x in enumerate(p)})]
    assert len(chain) == 20
    assert len([p for p in orders if ok(p, last=False)]) == 4
    assert [p for p in orders if ok(p)] == [tuple("CABED")]
    # Without "immediately", E, C, A, B, D would pass.
    p = "ECABD"
    assert p.index("C") < p.index("A") < p.index("B") and p.index("E") < p.index("D") and p[-1] != "B"


def test_q25():
    sols = [(a, 63 - a) for a in range(1, 63) if a > 63 - a and a == 2 * ((63 - a) - (a - (63 - a)))]
    assert sols == [(36, 27)]
    assert 36 - 27 == 9 and 27 - 9 == 18 and 36 == 2 * 18
    assert [(a, 70 - a) for a in range(1, 70) if a > 70 - a and a == 2 * (2 * (70 - a) - a)] == [(40, 30)]


def test_q26():
    seq = [1, 2, 4, 8, 16]
    assert poly_next(seq) == 31
    # Any sixth term: add c(n-1)(n-2)(n-3)(n-4)(n-5).
    n = sp.symbols("n")
    p = sp.interpolate(list(zip(range(1, 6), seq, strict=True)), n)
    assert p.subs(n, 6) == 31
    bump = (n - 1) * (n - 2) * (n - 3) * (n - 4) * (n - 5)
    for c in (0, 1, -2):
        q = p + c * bump
        assert [q.subs(n, k) for k in range(1, 6)] == seq
    assert (p + bump * sp.Rational(1, 120)).subs(n, 6) == 32
    assert [math.comb(k, 4) + math.comb(k, 2) + 1 for k in range(1, 7)] == [1, 2, 4, 8, 16, 31]
    # The formula needs no three chords through one point: a regular hexagon gives 30, six scattered points 31.
    def count_regions(angles):
        points = [(math.cos(a), math.sin(a)) for a in angles]
        chords = list(itertools.combinations(range(len(points)), 2))
        crossings = {}
        for (a, b), (c, d) in itertools.combinations(chords, 2):
            if len({a, b, c, d}) < 4:
                continue
            (x1, y1), (x2, y2), (x3, y3), (x4, y4) = points[a], points[b], points[c], points[d]
            den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
            if abs(den) < 1e-12:
                continue
            t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
            u = ((x1 - x3) * (y1 - y2) - (y1 - y3) * (x1 - x2)) / den
            if 1e-9 < t < 1 - 1e-9 and 1e-9 < u < 1 - 1e-9:
                at = (round(x1 + t * (x2 - x1), 7), round(y1 + t * (y2 - y1), 7))
                crossings[at] = crossings.get(at, 0) + 1
        # A point where m chords meet is C(m, 2) pairs, and it adds m - 1 regions.
        extra = sum(round((1 + math.sqrt(1 + 8 * pairs)) / 2) - 1 for pairs in crossings.values())
        return 1 + len(chords) + extra

    assert count_regions([2 * math.pi * i / 6 for i in range(6)]) == 30
    assert count_regions([0.1, 0.9, 2.0, 3.3, 4.1, 5.6]) == 31
    assert count_regions([0.1, 0.9, 2.0, 3.3, 4.1]) == 16


def test_q27():
    seq = [1, 4, 9, 7, 7, 9, 13, 10]
    assert [digit_sum(k * k) for k in range(1, 11)] == [*seq, 9, 1]
    assert differences(seq) == [3, 5, -2, 0, 2, 4, -3]
    assert not fits_simple_rule(seq)


def test_q28():
    seq = [1, 2, 3, 7, 22, 155]
    assert all(c == a * b + 1 for a, b, c in zip(seq, seq[1:], seq[2:], strict=False))
    assert 22 * 155 + 1 == 3411 and 22 * 155 == 3410
    assert [round(float(x), 2) for x in ratios(seq)] == [2.0, 1.5, 2.33, 3.14, 7.05]
    assert 3 - 2**2 == -1 and 7 - 3**2 == -2
    assert not fits_simple_rule(seq)
    # A linear recurrence a(n) = p a(n-1) + q a(n-2) that fits the first terms fails at 155.
    p, q = sp.symbols("p q")
    sol = sp.solve([p * 2 + q * 1 - 3, p * 3 + q * 2 - 7], [p, q])
    assert sol[p] * 7 + sol[q] * 3 == 8


def test_q29():
    cat = [math.comb(2 * n, n) // (n + 1) for n in range(0, 8)]
    assert cat[:6] == [1, 1, 2, 5, 14, 42] and cat[6] == 132
    r = ratios(cat[:6])
    assert r == [1, 2, F(5, 2), F(14, 5), 3]
    assert r == [F(4 * n - 2, n + 1) for n in range(1, 6)]
    assert [F(2, 2), F(6, 3), F(10, 4), F(14, 5), F(18, 6)] == r
    assert 42 * F(22, 7) == 132
    # Bell numbers.
    bell = [1]
    tri = [1]
    for _ in range(6):
        row = [tri[-1]]
        for x in tri:
            row.append(row[-1] + x)
        tri = row
        bell.append(tri[0])
    assert bell[:6] == [1, 1, 2, 5, 15, 52]
    assert [(3 ** (n - 1) + 1) // 2 for n in range(1, 6)] == [1, 2, 5, 14, 41]
    # Balanced brackets for n = 3.
    def brackets(n):
        out = []

        def go(s, o, c):
            if len(s) == 2 * n:
                out.append(s)
            if o < n:
                go(s + "(", o + 1, c)
            if c < o:
                go(s + ")", o, c + 1)

        go("", 0, 0)
        return out

    assert sorted(brackets(3)) == sorted(["((()))", "(()())", "(())()", "()(())", "()()()"])
    assert [len(brackets(n)) for n in range(1, 7)] == cat[1:7]


def test_q30():
    seq = [1, 2, 4, 8, 16, 22, 26, 38, 62, 74, 102]
    assert all(b == a + digit_product(a) for a, b in zip(seq, seq[1:], strict=False))
    assert differences(seq[5:-1])[:4] == [4, 12, 24, 12] and 22 - 16 == 6
    assert 16 + digit_sum(16) == 23
    assert digit_product(102) == 2 and 102 + 2 == 104
    assert not fits_simple_rule(seq[:-1])
