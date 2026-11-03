"""Every number printed in the answers of "Number Riddles": by direct computation and by the method in the answer."""
import itertools
import math
import sys
from fractions import Fraction as F

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)

NONNUMERIC = {}


def legendre(n, p):
    total, q = 0, p
    while q <= n:
        total += n // q
        q *= p
    return total


def to_base(n, b):
    out = []
    while n:
        out.append(n % b)
        n //= b
    return out[::-1] or [0]


def trailing_zeros(n, b):
    count = 0
    while n % b == 0:
        n //= b
        count += 1
    return count


def reachable(coins, limit):
    ok = [False] * (limit + 1)
    ok[0] = True
    for v in range(1, limit + 1):
        ok[v] = any(v >= c and ok[v - c] for c in coins)
    return ok


def test_q1():
    assert 36 * 6 == 216 and 4 * 30 + F(36, 2) == 138 and 216 - 138 == 78
    assert 216 - 120 == 96
    t = F(120) / F(11, 2)
    assert round(float(t), 2) == 21.82
    assert int(t) == 21 and round(float((t - 21) * 60)) == 49
    assert F(12, 11) * 60 == F(720, 11) and int(F(720, 11)) == 65
    assert round(float((F(720, 11) - 65) * 60)) == 27
    # A numerical check: at the coincidence the two angles agree.
    assert (4 * 30 + t / 2) % 360 == (t * 6) % 360


def test_q2():
    f = math.factorial(250)
    assert trailing_zeros(f, 10) == 62 == legendre(250, 5)
    assert 250 // 5 == 50 and 250 // 25 == 10 and 250 // 125 == 2
    assert trailing_zeros(math.factorial(24), 10) == 4
    assert trailing_zeros(math.factorial(25), 10) == 6
    assert all(trailing_zeros(math.factorial(n), 10) != 5 for n in range(1, 60))
    assert math.factorial(10) == 3628800


def test_q3():
    assert pow(7, 2026, 10) == 9
    assert [pow(7, k, 10) for k in range(1, 6)] == [7, 9, 3, 1, 7]
    assert 2026 == 4 * 506 + 2
    assert pow(7, 7, 4) == 3 and pow(7, 7**7, 10) == 3 and 7**3 == 343
    periods = {}
    for d in range(10):
        seq = [pow(d, k, 10) for k in range(1, 6)]
        periods[d] = next(p for p in (1, 2, 4) if seq[0] == seq[p])
    assert periods == {0: 1, 1: 1, 2: 4, 3: 4, 4: 2, 5: 1, 6: 1, 7: 4, 8: 4, 9: 2}


def divisors(n):
    return [d for d in range(1, n + 1) if n % d == 0]


def test_q4():
    doors = [False] * 1001
    for k in range(1, 1001):
        for j in range(k, 1001, k):
            doors[j] = not doors[j]
    opened = [i for i in range(1, 1001) if doors[i]]
    assert len(opened) == 31 and opened == [k * k for k in range(1, 32)]
    assert 31**2 == 961 and 32**2 == 1024
    assert len(divisors(72)) == 12 == 4 * 3 and 2**3 * 3**2 == 72 and not doors[72]
    counts = {n: len(divisors(n)) for n in range(1, 1000)}
    assert max(counts.values()) == 32
    assert min(n for n, c in counts.items() if c == 32) == 840 and not doors[840]


def test_q5():
    assert 1001 == 7 * 11 * 13 and 123123 == 123 * 1001
    for n in range(100, 1000):
        v = int(str(n) * 2)
        assert v == 1001 * n and v % 7 == v % 11 == v % 13 == 0
        assert v // 7 // 11 // 13 == n
    assert 123456 % 7 == 333 % 7 == 4 and 456 - 123 == 333
    for n in (123456, 987654, 1001001, 5551212):
        blocks, sign, s, m = [], 1, 0, n
        while m:
            blocks.append(m % 1000)
            s += sign * (m % 1000)
            sign, m = -sign, m // 1000
        for q in (7, 11, 13):
            assert n % q == s % q
    assert 4747 == 47 * 101 and all(101 % k for k in range(2, 11))


def test_q6():
    lcm = math.lcm(*range(2, 11))
    assert lcm == 2520 == 2**3 * 3**2 * 5 * 7
    n = lcm - 1
    assert n == 2519 and all(n % k == k - 1 for k in range(2, 11))
    assert all(any(m % k != k - 1 for k in range(2, 11)) for m in range(1, 2519))
    assert math.factorial(10) - 1 == 3628799
    assert math.lcm(*range(2, 21)) == 2**4 * 3**2 * 5 * 7 * 11 * 13 * 17 * 19 == 232792560
    # Going to 20 adds four primes and one power of 2, and no power of 3.
    small, large = math.lcm(*range(2, 11)), math.lcm(*range(2, 21))
    assert large // small == 2 * 11 * 13 * 17 * 19
    assert small % 9 == 0 and small % 27 != 0 and large % 27 != 0


def test_q7():
    f = math.factorial(20)
    assert trailing_zeros(f, 12) == 8
    assert legendre(20, 2) == 18 == 10 + 5 + 2 + 1
    assert legendre(20, 3) == 8 == 6 + 2
    assert legendre(20, 5) == 4
    assert 18 // 2 == 9 and min(9, 8) == 8
    assert trailing_zeros(f, 6) == 8 == min(18, 8)
    assert trailing_zeros(f, 10) == 4 == min(18, 4)
    # The trailing digits really are zeros in that base.
    assert to_base(f, 12)[-8:] == [0] * 8 and to_base(f, 12)[-9] != 0
    # The limiting prime can be the smaller: 9! has seven 2s and four 3s, and ends in 3 zeros in base 12, not 4.
    g = math.factorial(9)
    assert legendre(9, 2) == 7 and legendre(9, 3) == 4
    assert trailing_zeros(g, 12) == 3 == min(7 // 2, 4)


def test_q8():
    sols = [(a, b) for a in range(10) for b in range(10) if (40000 + 1000 * a + 270 + b) % 72 == 0]
    assert sols == [(3, 2)]
    assert 43272 == 72 * 601
    assert [b for b in range(10) if (270 + b) % 8 == 0] == [2]
    assert (15 + 3) % 9 == 0 and 4 + 3 + 2 + 7 + 2 == 18
    assert [(a, b) for a in range(10) for b in range(10) if (70360 + 1000 * a + b) % 72 == 0] == [(2, 0), (3, 8)]
    # A multiple of 6 and 12 need not be a multiple of 72.
    assert 12 % 6 == 0 and 12 % 72 != 0


def test_q9():
    assert pow(3, 2026, 17) == 8
    assert 3**2 == 9 and 81 % 17 == 13 and pow(3, 8, 17) == 16 and pow(3, 16, 17) == 1
    assert 2026 == 16 * 126 + 10
    assert (-9) % 17 == 8
    assert pow(2, 4, 17) == 16 and pow(2, 8, 17) == 1
    period = lambda a: next(k for k in range(1, 17) if pow(a, k, 17) == 1)  # noqa: E731
    assert period(3) == 16 and period(2) == 8
    assert all(period(a) in (1, 2, 4, 8, 16) for a in range(1, 17))


def test_q10():
    sols = [n for n in range(1, 2000) if all(n % k == 1 for k in (2, 3, 4, 5, 6)) and n % 7 == 0]
    assert sols[:2] == [301, 721]
    assert math.lcm(2, 3, 4, 5, 6) == 60 and 60 % 7 == 4 and 4 * 5 + 1 == 21 and 301 == 7 * 43
    assert math.lcm(60, 7) == 420 and 721 - 301 == 420
    assert 2 * 3 * 4 * 5 * 6 == 720
    assert [n for n in range(1, 106) if n % 3 == 2 and n % 5 == 3 and n % 7 == 2] == [23]
    assert 21 * 1 + 2 == 23


def test_q11():
    limit = 200
    ok = reachable((7, 11), limit)
    missing = [v for v in range(1, limit + 1) if not ok[v]]
    assert max(missing) == 59 == 7 * 11 - 7 - 11 and len(missing) == 30 == 6 * 10 // 2
    assert sorted(k * 11 % 7 for k in range(7)) == list(range(7))
    assert 66 - 7 == 59 and 66 == 6 * 11
    assert 7 * 11 - 1 == 76
    ok = reachable((6, 9), 500)
    assert all(not ok[v] for v in range(1, 501) if v % 3)
    assert all(ok[v] for v in range(6, 501) if v % 3 == 0)


def test_q12():
    text = "".join(str(n) for n in range(1, 1001))
    assert text.count("1") == 301
    assert sum(sum(map(int, str(n))) for n in range(1, 1000)) == 13500 == 3 * 100 * 45
    assert 100 * sum(range(10)) == 4500
    assert sum("1" in str(n) for n in range(0, 1000)) == 271 and 10**3 - 9**3 == 271
    assert sum("1" in str(n) for n in range(1, 1001)) == 272
    assert text.count("0") == 192
    assert sum(str(n).count("0") for n in range(10, 100)) == 9
    assert sum(str(n).count("0") for n in range(100, 1000)) == 180
    assert str(1000).count("0") == 3


def test_q13():
    weights = (1, 3, 9, 27)
    sums = {sum(s * w for s, w in zip(signs, weights, strict=True)) for signs in itertools.product((-1, 0, 1), repeat=4)}
    assert set(range(1, 41)) <= sums and max(sums) == 40
    assert (3**3 - 1) // 2 == 13 and (3**4 - 1) // 2 == 40
    assert 23 == 27 - 3 - 1 and 40 == 27 + 9 + 3 + 1 and 5 == 9 - 3 - 1
    # No three weights of any size reach all of 1 to 40.
    assert len({a * x + b * y + c * z for x, y, z in [(1, 3, 9)] for a, b, c in itertools.product((-1, 0, 1), repeat=3)}) == 27
    assert 2**5 - 1 == 31 and 2**6 - 1 == 63
    one_pan = {sum(c) for k in range(7) for c in itertools.combinations((1, 2, 4, 8, 16, 32), k)}
    assert set(range(1, 41)) <= one_pan


def test_q14():
    assert pow(3, 1000, 100) == 1
    assert 3**4 == 81 and 3**5 == 243 and 243 % 100 == 43
    assert 43**2 == 1849 and 49**2 == 2401
    assert pow(3, 10, 100) == 49 and pow(3, 20, 100) == 1
    assert next(k for k in range(1, 41) if pow(3, k, 100) == 1) == 20
    phi = sum(1 for k in range(1, 100) if math.gcd(k, 100) == 1)
    assert phi == 40
    assert pow(2, 1000, 100) == 76
    assert pow(2, 1000, 4) == 0 and pow(2, 1000, 25) == 1
    assert next(k for k in range(1, 21) if pow(2, k, 25) == 1) == 20
    assert [n for n in range(100) if n % 4 == 0 and n % 25 == 1] == [76]


def highest_power(n, p):
    k = 0
    while n % p == 0:
        n //= p
        k += 1
    return k


def carries(a, b, p):
    c, count = 0, 0
    while a or b or c:
        c = 1 if a % p + b % p + c >= p else 0
        count += c
        a //= p
        b //= p
    return count


def test_q15():
    c = math.comb(100, 50)
    assert highest_power(c, 2) == 3 and highest_power(c, 3) == 4 and c % 7 != 0
    assert legendre(100, 2) == 97 == 50 + 25 + 12 + 6 + 3 + 1 and legendre(50, 2) == 47 == 25 + 12 + 6 + 3 + 1
    assert legendre(100, 3) == 48 and legendre(50, 3) == 22 and 48 - 44 == 4
    assert legendre(100, 7) == 16 == 14 + 2 and legendre(50, 7) == 8 == 7 + 1
    assert to_base(50, 7) == [1, 0, 1] and to_base(100, 7) == [2, 0, 2]
    assert carries(50, 50, 7) == 0 and carries(50, 50, 2) == 3 and carries(50, 50, 3) == 4
    assert to_base(50, 2) == [1, 1, 0, 0, 1, 0]
    for n in range(1, 40):
        assert math.comb(2 * n, n) == 2 * math.comb(2 * n - 1, n - 1)


def primes(limit):
    return [p for p in range(2, limit) if all(p % q for q in range(2, int(math.isqrt(p)) + 1))]


def test_q16():
    ps = [p for p in primes(5000) if p > 3]
    assert all((p * p - 1) % 24 == 0 for p in ps)
    assert 5**2 - 1 == 24 and 7**2 - 1 == 48 and math.gcd(24, 48) == 24
    assert all((n * n - 1) % 24 == 0 for n in range(1, 5000) if math.gcd(n, 6) == 1)
    assert 25**2 - 1 == 624 == 24 * 26
    assert all((p**4 - 1) % 240 == 0 for p in ps if p > 5)
    assert 16 * 3 * 5 == 240


def test_q17():
    assert [n for n in range(1000, 10000) if 4 * n == int(str(n)[::-1])] == [2178]
    assert 4 * 2178 == 8712
    assert [(b, c) for b in range(10) for c in range(10) if 13 * b + 1 == 2 * c] == [(1, 7)]
    for b, c in itertools.product(range(10), repeat=2):
        left = 4 * (2008 + 100 * b + 10 * c)
        assert (left == 8002 + 100 * c + 10 * b) == (13 * b + 1 == 2 * c)
    assert [n for n in range(1000, 10000) if 9 * n == int(str(n)[::-1])] == [1089]
    assert 9 * 1089 == 9801 and 4 * 21978 == 87912 and 9 * 10989 == 98901


def test_q18():
    nums = [F(100 * a + 10 * b + c, 999) for a, b, c in itertools.permutations(range(10), 3)]
    assert len(nums) == 720 == 10 * 9 * 8
    assert sum(nums) == 360
    for a, b, c in itertools.permutations(range(10), 3):
        partner = F(100 * (9 - a) + 10 * (9 - b) + (9 - c), 999)
        assert partner + F(100 * a + 10 * b + c, 999) == 1
        assert partner != F(100 * a + 10 * b + c, 999)
    assert F(720) * F(4995, 10) / 999 == 360
    assert sum(1 for a, b, c in itertools.permutations(range(10), 3) if a == 3) == 72
    two = [F(10 * a + b, 99) for a, b in itertools.permutations(range(10), 2)]
    assert len(two) == 90 and sum(two) == 45


def test_q19():
    moments = [F(k, 143) for k in range(143)]
    swap_valid = [t for t in moments if (12 * (12 * t % 1)) % 1 == t]
    assert len(swap_valid) == 143
    same = [t for t in moments if 12 * t % 1 == t]
    assert len(same) == 11 and all((11 * t).denominator == 1 for t in same)
    ambiguous = [t for t in moments if 12 * t % 1 != t]
    assert len(ambiguous) == 132 == 143 - 11
    pairs = {frozenset((t, 12 * t % 1)) for t in ambiguous}
    assert len(pairs) == 66 and all(len(p) == 2 for p in pairs)
    # The printed example: t = 1/143 of 12 hours.
    minutes = F(1, 143) * 720
    assert int(minutes) == 5 and round(float((minutes - 5) * 60)) == 2
    s = F(12, 143) * 720
    assert int(s // 60) == 1 and int(s % 60) == 0 and round(float((s % 60) * 60)) == 25
    assert 144 % 143 == 1


def test_q20():
    limit = 500
    ok = reachable((6, 9, 20), limit)
    missing = [v for v in range(1, limit + 1) if not ok[v]]
    assert max(missing) == 43
    smallest = {r: min(v for v in range(limit + 1) if ok[v] and v % 6 == r) for r in range(6)}
    assert smallest == {0: 0, 1: 49, 2: 20, 3: 9, 4: 40, 5: 29}
    assert 49 == 9 + 40 and 40 == 20 + 20 and 29 == 9 + 20 and 49 - 6 == 43
    assert all(v >= smallest[v % 6] for v in range(44, 200))
    assert 9 % 6 == 3 and 20 % 6 == 2
    assert 44 == 20 + 6 * 4 and 45 == 9 * 5 and 46 == 20 + 20 + 6
    assert 47 == 20 + 9 * 3 and 48 == 6 * 8 and 49 == 20 + 20 + 9
    assert 9 * 20 - 9 - 20 == 151
    ok2 = reachable((9, 20), limit)
    assert max(v for v in range(1, limit + 1) if not ok2[v]) == 151


def ways(n):
    out = []
    for k in range(2, 2 * n):
        rest = 2 * n - k * (k - 1)
        if rest <= 0:
            break
        if rest % (2 * k) == 0:
            out.append((rest // (2 * k), k))
    return out


def test_q21():
    for n in range(1, 2000):
        is_power = n & (n - 1) == 0
        assert (len(ways(n)) == 0) == is_power, n
        odd = [d for d in range(3, n + 1, 2) if n % d == 0]
        assert len(ways(n)) == len(odd), n
    assert ways(2026) == [(505, 4)] and 505 + 506 + 507 + 508 == 2026
    assert 2026 == 2 * 1013 and 1013 in primes(1100) and 2 * 505 + 3 == 1013
    assert sorted(ways(15)) == sorted([(7, 2), (4, 3), (1, 5)])
    assert 7 + 8 == 15 and 4 + 5 + 6 == 15 and sum(range(1, 6)) == 15


def josephus(n, step):
    people = list(range(1, n + 1))
    i = 0
    while len(people) > 1:
        i = (i + step - 1) % len(people)
        people.pop(i)
    return people[0]


def test_q22():
    assert josephus(100, 2) == 73
    assert 100 == 64 + 36 and 2 * 36 + 1 == 73 and 2 * 36 == 72
    for n in range(1, 300):
        a = int(math.log2(n))
        assert josephus(n, 2) == 2 * (n - 2**a) + 1
        assert int(bin(n)[3:] + "1", 2) == josephus(n, 2)
    for a in range(1, 8):
        assert josephus(2**a, 2) == 1
    assert bin(100)[2:] == "1100100" and bin(73)[2:] == "1001001"
    j = 0
    for k in range(2, 101):
        j = (j + 3) % k
    assert j + 1 == josephus(100, 3) == 91
    # After 36 have gone, person 72 was the last to leave, and 64 remain.
    people = list(range(1, 101))
    i, gone = 1, []
    while len(gone) < 36:
        gone.append(people.pop(i))
        i = (i + 1) % len(people)
    assert gone[-1] == 72 and len(people) == 64 and people[i - 1] == 73
    # Person 1 lasts two passes: 25 are left, that pass ends on person 97 staying, and person 1 goes next.
    circle, order, i = list(range(1, 101)), [], 1
    while len(circle) > 1:
        order.append(circle.pop(i))
        i = (i + 1) % len(circle)
    assert order[:50] == list(range(2, 101, 2)) and order[75 + 11] == 93 and order[75 + 12] == 1
    assert circle == [73]


def doubles(n):
    s = str(n)
    return int(s[-1] + s[:-1]) == 2 * n and s[-1] != "0"


def test_q23():
    n = 105263157894736842
    assert doubles(n) and 2 * n == 210526315789473684 and len(str(n)) == 18
    # 10^m = 2 modulo 19 first at m = 17.
    assert next(m for m in range(1, 40) if pow(10, m, 19) == 2) == 17
    a1 = (10**17 - 2) // 19
    assert (10**17 - 2) % 19 == 0 and len(str(a1)) == 16
    a2 = 2 * a1
    assert a2 == 10526315789473684 and len(str(a2)) == 17 and n == 10 * a2 + 2
    # No smaller number, by the same equation for every length up to 18 and every last digit.
    best = []
    for length in range(2, 19):
        for d in range(1, 10):
            value = d * (10 ** (length - 1) - 2)
            if value % 19 == 0:
                a = value // 19
                if len(str(a)) == length - 1:
                    best.append(10 * a + d)
    assert min(best) == n
    assert all(not doubles(k) for k in range(1, 100000))
    # The doubling construction from the right.
    digits, carry, d = [2], 0, 2
    while True:
        p = 2 * d + carry
        d, carry = p % 10, p // 10
        if d == 1 and carry == 0:
            digits.append(1)
            break
        digits.append(d)
    built = int("".join(map(str, digits[::-1])))
    assert built == n
    # Repeating block of 2/19.
    assert (2 * 10**18 // 19) == n and 2 * 10**18 % 19 == 2
    # Tripling: 10^m = 3 modulo 29 first at m = 27.
    assert next(m for m in range(1, 40) if pow(10, m, 29) == 3) == 27
    t = 1034482758620689655172413793
    assert len(str(t)) == 28 and int(str(t)[-1] + str(t)[:-1]) == 3 * t
    assert t == 10 * (3 * (10**27 - 3) // 29) + 3
    # The 1 is written, and only one with no carry out stops it: an earlier 1 carries, and stopping there fails.
    assert digits[-1] == 1 and 2 * digits[-1] == digits[0]
    early = digits.index(1)
    assert early < len(digits) - 1
    assert not doubles(int("".join(map(str, digits[: early + 1][::-1]))))


def test_q24():
    big = 4444**4444
    a = sum(map(int, str(big)))
    b = sum(map(int, str(a)))
    c = sum(map(int, str(b)))
    assert (a, b, c) == (72601, 16, 7)
    assert 4444 % 9 == 7 and sum(map(int, "4444")) == 16
    assert [pow(7, k, 9) for k in range(1, 5)] == [7, 4, 1, 7]
    assert 4444 % 3 == 1 and big % 9 == 7
    assert 4 * 4444 == 17776 and 9 * 17776 == 159984
    assert len(str(big)) <= 17776
    assert max(sum(map(int, str(v))) for v in range(1, 159985)) <= 1 + 5 * 9 == 46
    assert max(sum(map(int, str(v))) for v in range(1, 47)) == 12
    assert sum(map(int, "39")) == 12
    assert [v for v in range(1, 13) if v % 9 == 7] == [7]
    assert round(a / len(str(big)), 1) in (4.5, 4.4, 4.6)


def coconuts(n, leftover=0):
    x = n
    for _ in range(5):
        if x % 5 != 1:
            return False
        x = (x - 1) // 5 * 4
    return x % 5 == leftover


def test_q25():
    assert next(n for n in range(1, 10000) if coconuts(n)) == 3121
    piles, x = [3121], 3121
    for _ in range(5):
        x = (x - 1) // 5 * 4
        piles.append(x)
    assert piles == [3121, 2496, 1996, 1596, 1276, 1020] and 1020 == 5 * 204
    assert F(4, 5) * (-4 - 1) == -4
    assert 5**5 == 3125 and 4**5 == 1024 and 3125 - 4 == 3121
    for k in range(1, 8):
        final = 1024 * k - 4
        assert (final % 5 == 0) == (k % 5 == 1)
        assert (final % 5 == 1) == (k % 5 == 0)
    assert next(n for n in range(1, 20000) if coconuts(n, leftover=1)) == 15621 == 5**6 - 4
