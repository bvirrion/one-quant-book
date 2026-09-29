"""Numbers gate: every numerical answer printed in Book 18, chapter 4 (text and solutions)."""
import pathlib
import random
import sys
from fractions import Fraction

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_oa import (
    breakeven_confidence,
    item_value,
    next_by_differences,
    pass_probability,
    plan_score,
    pump_value,
    seating_solutions,
)
from iv_oa_code import PriceWindowCounter, count_oracle, longest_rising_run, longest_rising_run_oracle


def test_hook_and_text():
    assert 8 * 60 / 80 == 6  # seconds per item
    assert breakeven_confidence(1) == Fraction(1, 2)
    assert breakeven_confidence(Fraction(1, 4)) == Fraction(1, 5)
    # random guessing on five options under a quarter-mark penalty is worth exactly zero
    assert item_value(Fraction(1, 5), Fraction(1, 4)) == 0
    # the hook: answering everything against skipping the weakest fifth (text example)
    all_in = 64 * item_value(Fraction(95, 100), 1) + 16 * item_value(Fraction(35, 100), 1)
    skip = 64 * item_value(Fraction(95, 100), 1)
    assert all_in == Fraction(528, 10) and skip == Fraction(576, 10)


def test_q1_arithmetic():
    assert Fraction(48) * Fraction(35, 100) == Fraction(168, 10)
    assert Fraction(7, 8) - Fraction(2, 3) == Fraction(5, 24)
    assert round(5 / 24, 4) == 0.2083
    assert Fraction(24, 10) / Fraction(16, 1000) == 150


def test_q2_sequences():
    assert next_by_differences([3, 8, 15, 24, 35]) == 48
    s = [2, 3, 5, 9, 17]
    assert all(b == 2 * a - 1 for a, b in zip(s, s[1:], strict=False)) and 2 * 17 - 1 == 33
    inter = [1, 4, 2, 8, 3, 12, 4]
    assert inter[0::2] == [1, 2, 3, 4] and inter[1::2] == [4, 8, 12] and 16 == 4 * 4


def test_q3_negative_marking():
    w = Fraction(1, 2)
    assert breakeven_confidence(w) == Fraction(1, 3)
    assert item_value(Fraction(1, 4), w) == Fraction(-1, 8)
    assert item_value(Fraction(1, 3), w) == 0
    assert item_value(Fraction(1, 2), w) == Fraction(1, 4)


def test_q4_rising_run():
    assert longest_rising_run([]) == 0
    assert longest_rising_run([5]) == 1
    assert longest_rising_run([1, 2, 2, 3]) == 2
    assert longest_rising_run([3, 2, 1]) == 1
    assert longest_rising_run([100, 101, 103, 102, 104, 105, 106, 99]) == 4
    for seed in range(300):
        rng = random.Random(seed)
        xs = [rng.randint(0, 5) for _ in range(rng.randint(0, 40))]
        assert longest_rising_run(xs) == longest_rising_run_oracle(xs)


def test_q5_plan():
    n_hard, score = plan_score(60, 5, Fraction(97, 100), 12, Fraction(7, 10), 480, 1)
    assert n_hard == 15 and score == Fraction(624, 10)
    n_hard, score = plan_score(60, 5, Fraction(97, 100), 12, Fraction(45, 100), 480, 1)
    assert n_hard == 0 and score == Fraction(564, 10)


def test_q6_probability():
    primes = {2, 3, 5, 7, 11}
    n = sum((a + b) in primes for a in range(1, 7) for b in range(1, 7))
    assert Fraction(n, 36) == Fraction(5, 12)
    heads = sum(sum(t) >= 2 for t in __import__("itertools").product([0, 1], repeat=3))
    assert Fraction(heads, 8) == Fraction(1, 2)


def test_q7_seating():
    assert seating_solutions() == ["CADEB"]
    assert seating_solutions()[0][2] == "D"


def test_q8_pump():
    vals = {k: pump_value(k, 64) for k in range(0, 65)}
    k_best = max(vals, key=vals.get)
    assert k_best == 32 and vals[32] == 16
    assert pump_value(20, 64) == Fraction(55, 4)  # 13.75


def test_q9_window_counter():
    c = PriceWindowCounter([101, 99, 100, 100, 105])
    assert c.count(100, 101) == 3 and c.count(106, 200) == 0 and c.count(101, 100) == 0
    for seed in range(200):
        rng = random.Random(seed)
        xs = [rng.randint(0, 50) for _ in range(rng.randint(0, 60))]
        c = PriceWindowCounter(xs)
        for _ in range(20):
            lo, hi = rng.randint(-5, 55), rng.randint(-5, 55)
            assert c.count(lo, hi) == count_oracle(xs, lo, hi)


def test_q10_retest():
    assert round(pass_probability(57, 60, 5), 3) == 0.274
    assert round(pass_probability(57, 60, 5, attempts=2), 3) == 0.473
    # with a practice gain of a quarter of the between-candidate spread (spread 8): +2 points
    assert round(pass_probability(59, 60, 5), 3) == 0.421
    assert round(0.26 * 8, 1) == 2.1


def test_figure_csv(tmp_path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "fig_iv_skip", pathlib.Path(__file__).resolve().parents[1] / "python" / "fig_iv_skip.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.OUT = tmp_path
    m.main()
    lines = (tmp_path / "skip.csv").read_text().splitlines()
    assert lines[0] == "p,w0,w025,w1" and len(lines) == 52
    assert lines[26].startswith("0.50,0.5000,0.3750,0.0000")


def test_example_differences():
    assert next_by_differences([2, 6, 12, 20, 30]) == 42
    assert all(n * (n + 1) == v for n, v in zip(range(1, 6), [2, 6, 12, 20, 30], strict=True))


def _pairs_hash(prices, target):
    seen, count = {}, 0
    for p in prices:
        count += seen.get(target - p, 0)
        seen[p] = seen.get(p, 0) + 1
    return count


def _pairs_brute(prices, target):
    n = len(prices)
    return sum(prices[i] + prices[j] == target for i in range(n) for j in range(i + 1, n))


def test_worked_answers():
    assert 30 * 60 // 60 == 30 and 20 * 30 == 600  # item 20 due at ten minutes
    assert (30 - 12) * 60 // 40 == 27
    assert 10**5 * 10**5 // 2 == 5 * 10**9
    assert _pairs_hash([3, 5, 2, 5, 1], 7) == 2 == _pairs_brute([3, 5, 2, 5, 1], 7)
    for s in range(300):
        r = random.Random(s)
        xs = [r.randint(-5, 9) for _ in range(r.randint(0, 25))]
        t = r.randint(-4, 12)
        assert _pairs_hash(xs, t) == _pairs_brute(xs, t)
    n = 10**5
    assert _pairs_hash([4] * 1000, 8) == 1000 * 999 // 2
    assert n * (n - 1) // 2 > 2**31 - 1
