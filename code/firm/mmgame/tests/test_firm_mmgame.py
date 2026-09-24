"""Acceptance tests of the Book 2, Chapter 30 build (market-making game engine)."""
import math
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_mmgame import Table, card_sum_distribution, deal, expected_pnl, mean, play, update


def test_card_sum_distribution():
    d = card_sum_distribution(5)
    assert abs(sum(d.values()) - 1) < 1e-12 and abs(mean(d) - 35.0) < 1e-9
    assert min(d) == 1 + 1 + 1 + 1 + 2 and max(d) == 13 + 13 + 13 + 13 + 12      # at most four of a value
    one = card_sum_distribution(1)
    assert all(abs(p - 1 / 13) < 1e-12 for p in one.values())


def test_update_moves_the_mean_towards_the_trade():
    t, prior = Table(), card_sum_distribution(5)
    m = mean(prior)
    assert mean(update(prior, "buy", m - 2, m + 2, t, 4.0)) > m
    assert mean(update(prior, "sell", m - 2, m + 2, t, 4.0)) < m


def test_no_informed_no_loss_on_average():
    t = Table(informed=0.0)
    [(_, m, se)] = expected_pnl([6.0], t, games=400, seed=1)
    assert m > 0 and abs(m - 20 * math.exp(-6 / 8) * 3.0) < 4 * se + 1e-9


def test_learning_beats_not_learning_against_informed():
    t = Table(informed=0.3)
    [(_, learn, _)] = expected_pnl([4.0], t, games=400, seed=2, learn=True)
    [(_, naive, _)] = expected_pnl([4.0], t, games=400, seed=2, learn=False)
    assert learn > naive


def test_play_is_seeded():
    t = Table()
    prior = card_sum_distribution(t.cards)
    v, d = deal(t, random.Random(5), prior)
    assert (v, d) == deal(t, random.Random(5), prior) and play(4.0, t, v, d)[0] == play(4.0, t, v, d)[0]
