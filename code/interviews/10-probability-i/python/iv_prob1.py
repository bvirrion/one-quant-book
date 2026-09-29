"""Book 18, chapter 10: probability I, by exhaustive enumeration with exact fractions."""
from fractions import Fraction
from itertools import combinations, permutations, product
from math import comb, factorial


def arrangements(word: str) -> int:
    counts = {c: word.count(c) for c in set(word)}
    out = factorial(len(word))
    for k in counts.values():
        out //= factorial(k)
    return out


def at_least_one(p, n):
    return 1 - (1 - Fraction(p)) ** n


def multisets(items: int, boxes: int, at_least_one_each: bool = False) -> int:
    """Stars and bars: ways to put `items` identical items into `boxes` labelled boxes."""
    if at_least_one_each:
        return comb(items - 1, boxes - 1)
    return comb(items + boxes - 1, boxes - 1)


def no_collision(n_ids: int, space: int) -> Fraction:
    p = Fraction(1)
    for k in range(n_ids):
        p *= Fraction(space - k, space)
    return p


def bayes(prior, sensitivity, false_positive) -> Fraction:
    prior, s, f = Fraction(prior), Fraction(sensitivity), Fraction(false_positive)
    return s * prior / (s * prior + f * (1 - prior))


def two_dice_protocols():
    """P(both six | report), for 'at least one six' (protocol A) and 'a random die shows six' (protocol B)."""
    rolls = list(product(range(1, 7), repeat=2))
    a_cond = [r for r in rolls if 6 in r]
    pa = Fraction(sum(r == (6, 6) for r in a_cond), len(a_cond))
    num = den = Fraction(0)
    for r in rolls:
        for i in (0, 1):
            w = Fraction(1, 36) * Fraction(1, 2)
            if r[i] == 6:
                den += w
                num += w * (r == (6, 6))
    return pa, num / den


def first_ace_position(deck_size: int = 52, aces: int = 4) -> Fraction:
    return Fraction(deck_size + 1, aces + 1)


def first_ace_position_brute(deck_size: int, aces: int) -> Fraction:
    total = 0
    count = 0
    for pos in combinations(range(deck_size), aces):
        total += min(pos) + 1
        count += 1
    return Fraction(total, count)


def ticket_boxes():
    """Boxes WW, WL, LL, WWL; pick a box at random, draw a ticket at random: it is W. Chance that a second
    ticket drawn at random from the same box (without replacement) is W."""
    boxes = ["WW", "WL", "LL", "WWL"]
    num = den = Fraction(0)
    for b in boxes:
        for i, first in enumerate(b):
            w = Fraction(1, len(boxes)) * Fraction(1, len(b))
            if first != "W":
                continue
            rest = b[:i] + b[i + 1 :]
            den += w
            num += w * Fraction(rest.count("W"), len(rest))
    return num / den


def four_doors_switch() -> tuple:
    """Four doors, one prize. You pick door 0; the host opens an empty door at random among the other three;
    you switch to one of the two remaining closed doors at random. Returns (stay, switch)."""
    stay = sw = Fraction(0)
    for prize in range(4):
        empties = [d for d in (1, 2, 3) if d != prize]
        for opened in empties:
            w = Fraction(1, 4) * Fraction(1, len(empties))
            stay += w * (prize == 0)
            choices = [d for d in (1, 2, 3) if d != opened]
            for c in choices:
                sw += w * Fraction(1, len(choices)) * (c == prize)
    return stay, sw


def monday_positions():
    """Two positions, each profitable with probability 1/2 and opened on a uniform day of 7, independently.
    P(both profitable | at least one is profitable and was opened on Monday (day 0))."""
    states = list(product([0, 1], range(7), [0, 1], range(7)))
    cond = [s for s in states if (s[0] == 1 and s[1] == 0) or (s[2] == 1 and s[3] == 0)]
    return Fraction(sum(s[0] == 1 and s[2] == 1 for s in cond), len(cond))


def meet_within(window: float, total: float) -> Fraction:
    return 1 - Fraction(total - window, total) ** 2


def rank_probabilities(n: int = 6):
    perms = list(permutations(range(n)))
    a_beats_b = Fraction(sum(p.index(0) < p.index(1) for p in perms), len(perms))
    a_best = Fraction(sum(p[0] == 0 for p in perms), len(perms))
    a_beats_bc = Fraction(sum(p.index(0) < min(p.index(1), p.index(2)) for p in perms), len(perms))
    return a_beats_b, a_best, a_beats_bc
