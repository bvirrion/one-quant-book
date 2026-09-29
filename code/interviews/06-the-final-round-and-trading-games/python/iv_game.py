"""Book 18, chapter 6: the card-sum market and the other games of the chapter, exactly.

Deck: 52 cards, four of each value 1 (ace) to 13 (king). The market is on the sum of three cards
drawn without replacement.
"""
from fractions import Fraction
from functools import cache
from itertools import combinations
from math import log

DECK = [v for v in range(1, 14) for _ in range(4)]


def sum_distribution(deck=None, k=3):
    """Exact distribution of the sum of k cards drawn without replacement: {sum: probability}."""
    deck = DECK if deck is None else deck
    counts = {}
    n = 0
    for c in combinations(range(len(deck)), k):
        s = sum(deck[i] for i in c)
        counts[s] = counts.get(s, 0) + 1
        n += 1
    return {s: Fraction(c, n) for s, c in counts.items()}


def mean_var(dist):
    m = sum(s * p for s, p in dist.items())
    v = sum((s - m) ** 2 * p for s, p in dist.items())
    return m, v


def fair_after(revealed, k=3):
    """Expected sum of k cards when the cards in `revealed` are known to be among them."""
    rest_total = sum(DECK) - sum(revealed)
    rest_n = len(DECK) - len(revealed)
    return sum(revealed) + (k - len(revealed)) * Fraction(rest_total, rest_n)


def fair_given_one_above(threshold, k=3):
    """Expected sum when one of the k cards is known only to exceed `threshold`."""
    high = [v for v in range(threshold + 1, 14)]
    return sum(Fraction(1, len(high)) * fair_after([v], k) for v in high)


def informed_loss(half_width, k=3):
    """Expected loss per opportunity to a player who sees one card and trades against a market centred
    on the unconditional fair value whenever the market is wrong in their favour."""
    centre = fair_after([], k)
    loss = Fraction(0)
    for v in range(1, 14):
        f = fair_after([v], k)
        loss += Fraction(1, 13) * (max(f - (centre + half_width), 0) + max((centre - half_width) - f, 0))
    return loss


def kelly_fraction(p):
    return 2 * p - 1


def log_growth(p, f):
    return p * log(1 + f) + (1 - p) * log(1 - f)


@cache
def red_card_value(red: int, black: int) -> Fraction:
    """Best chance of winning a bet 'the next card is red', stopping when you choose (must stop by the last card)."""
    if red + black == 0:
        return Fraction(0)
    stop = Fraction(red, red + black)
    if red + black == 1:
        return stop
    cont = Fraction(0)
    if red:
        cont += Fraction(red, red + black) * red_card_value(red - 1, black)
    if black:
        cont += Fraction(black, red + black) * red_card_value(red, black - 1)
    return max(stop, cont)
