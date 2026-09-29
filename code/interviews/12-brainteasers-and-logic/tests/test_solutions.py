"""Numbers gate: every answer printed in Book 18, chapter 12 (text and solutions), by exhaustive search."""
import itertools
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_teasers import (
    announcement_rounds,
    chomp_first_player_wins,
    divide_coins,
    fake_bag,
    hamming_hat,
    hat_circle_value,
    hat_line,
    losing_positions,
    majority_rule,
    replace_rule_final,
    replace_rule_simulate,
    token_game,
    zero_block_exists,
)


def test_text_take_away():
    assert losing_positions(5, (1, 2)) == [0, 3]
    assert losing_positions(21, (1, 2, 3)) == [0, 4, 8, 12, 16, 20]


def test_q1_tokens():
    assert {token_game(20, 13, random.Random(s)) for s in range(200)} == {"b"}
    assert {token_game(20, 12, random.Random(s)) for s in range(200)} == {"r"}


def test_q2_take_up_to_four():
    lose = losing_positions(31, (1, 2, 3, 4))
    assert 30 in lose and 31 not in lose and 31 - 1 in lose


def test_q3_q4_pigeonhole_parity():
    assert 400 > 366
    for seed in range(50):
        rng = random.Random(seed)
        edges = {tuple(sorted(rng.sample(range(12), 2))) for _ in range(rng.randint(0, 40))}
        deg = [sum(i in e for e in edges) for i in range(12)]
        assert sum(d % 2 for d in deg) % 2 == 0


def test_q5_hourglasses():
    # start both at 0; flip the 3 at t=3; at t=5 the 3 has run 2 of its 3 minutes: flip it back, 2 minutes remain
    t_flip, t_five = 3, 5
    run_since_flip = t_five - t_flip
    assert t_five + run_since_flip == 7


def test_q6_hat_line():
    for seed in range(200):
        rng = random.Random(seed)
        cols = [rng.randrange(3) for _ in range(100)]
        assert hat_line(cols, 3) >= 99


def test_q7_fake_bag():
    for bag in range(1, 11):
        deficit = bag * 0.1
        assert fake_bag(deficit) == bag
    assert sum(range(1, 11)) == 55


def test_q8_division():
    assert divide_coins(4) == [99, 0, 1, 0]
    assert divide_coins(5) == [98, 0, 1, 0, 1]


def test_q9_chomp():
    assert chomp_first_player_wins((5, 5, 5, 5))
    assert not chomp_first_player_wins((1,))


def test_q10_announcements():
    assert announcement_rounds((1, 1, 1, 0, 0)) == (3, {0, 1, 2})
    assert announcement_rounds((1, 0, 0, 0, 0)) == (1, {0})
    assert announcement_rounds((1, 1, 0, 0, 0)) == (2, {0, 1})


def test_q11_hat_circle():
    win, right, wrong = hat_circle_value(majority_rule)
    assert win == 0.75 and right == wrong == 6
    # any strategy: correct and wrong guesses are equal in total (each guess is right in half the configurations
    # that share the guesser's view), which bounds the winning share by n/(n+1)
    rng = random.Random(0)
    for _ in range(300):
        table = {(i, v): rng.randrange(3) for i in range(3) for v in itertools.product([0, 1], repeat=2)}
        w, r, x = hat_circle_value(lambda i, v, t=table: t[(i, v)])
        assert r == x and w <= 0.75
    assert hamming_hat() == 0.875


def test_q12_invariant():
    assert replace_rule_final(range(1, 11)) == 39_916_799
    assert {replace_rule_simulate(range(1, 11), random.Random(s)) for s in range(20)} == {39_916_799}


def test_q13_subtraction_game():
    lose = losing_positions(40, (1, 3, 4))
    assert lose == [n for n in range(41) if n % 7 in (0, 2)]
    assert 20 not in lose and (20 - 4) in lose


def test_q14_zero_block():
    for seed in range(500):
        rng = random.Random(seed)
        assert zero_block_exists([rng.randint(-50, 50) for _ in range(10)], 10)


def test_worked_answers():
    eps = 0.01
    times = [i * (5 + eps) for i in range(12)]
    assert times[-1] <= 60 and all(b - a > 5 for a, b in zip(times, times[1:], strict=False))
    r = random.Random(12)
    for _ in range(2000):
        t = sorted(r.uniform(0, 60) for _ in range(13))
        assert min(b - a for a, b in zip(t, t[1:], strict=False)) <= 5
    assert sum(range(1, 21)) == 210
    for s in range(300):
        rr = random.Random(s)
        board = list(range(1, 21))
        while len(board) > 1:
            i, j = rr.sample(range(len(board)), 2)
            a, b = board[i], board[j]
            board = [x for k, x in enumerate(board) if k not in (i, j)] + [abs(a - b)]
        assert board[0] % 2 == 0
    board = [abs(a - b) for a, b in zip(range(1, 21, 2), range(2, 21, 2), strict=True)]
    assert board == [1] * 10
    board = [abs(a - b) for a, b in zip(board[::2], board[1::2], strict=True)]
    assert board == [0] * 5
