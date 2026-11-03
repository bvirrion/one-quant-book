"""Behavioural and Fit: most answers are advice with no number to check. The two that print numbers are tested here."""
import math
from functools import cache

import numpy as np

_ADVICE = "advice on how to answer, with an illustration and blanks; nothing is calculated or stated as fact"
NONNUMERIC = {
    1: "advice on self-presentation; " + _ADVICE,
    2: "motivation; " + _ADVICE,
    3: "role choice; " + _ADVICE,
    4: "type of firm, with a rough comparison the reader is told to check; " + _ADVICE,
    5: "research on a firm; " + _ADVICE,
    6: "self-assessment; " + _ADVICE,
    7: "career plan; " + _ADVICE,
    8: "making a case; " + _ADVICE,
    9: "plain explanation with an invented round-number analogy; " + _ADVICE,
    10: "explaining a weak spot; " + _ADVICE,
    11: "other offers; " + _ADVICE,
    12: "games and betting; " + _ADVICE,
    13: "self-teaching; " + _ADVICE,
    14: "questions to ask; " + _ADVICE,
    15: "disappointing project; " + _ADVICE,
    16: "own mistake; " + _ADVICE,
    17: "correcting a report; order of actions; " + _ADVICE,
    18: "disagreement; " + _ADVICE,
    19: "doubting a result; " + _ADVICE,
    20: "teamwork; " + _ADVICE,
    21: "release under pressure; judgement; " + _ADVICE,
    22: "production failure; " + _ADVICE,
    23: "deadline; " + _ADVICE,
    25: "personal risk; " + _ADVICE,
    27: "loss limit; judgement; " + _ADVICE,
    28: "broken rule; judgement; " + _ADVICE,
    29: "suspected mismarking; judgement; " + _ADVICE,
    30: "being told you are wrong; " + _ADVICE,
}


def test_q24():
    def gap(w):
        return math.log(w + 1) - 0.5 * math.log(w + 3) - 0.5 * math.log(w)

    assert abs(gap(1.0)) < 1e-12
    assert gap(0.1) > 0 and gap(10.0) < 0

    def certainty(w):
        return math.sqrt((w + 3) * w) - w

    assert round(certainty(10), 2) == 1.40
    assert round(certainty(1.0), 2) == 1.0
    assert round(certainty(0.1), 2) == 0.46
    assert round(certainty(1000), 2) == 1.5
    assert 0.5 * 3 == 1.5
    rng = np.random.default_rng(24)
    heads = rng.random(1_000_000) < 0.5
    assert abs(np.where(heads, 3.0, 0.0).mean() - 1.5) < 0.005
    assert abs(np.log(1.0 + np.where(heads, 3.0, 0.0)).mean() - math.log(2)) < 0.002


def stats(gain, p, loss):
    mean = p * gain - (1 - p) * loss
    var = p * gain**2 + (1 - p) * loss**2 - mean**2
    return mean, math.sqrt(var)


def longest_run_cdf(n, p_lose, k):
    """Probability that the longest run of losing days in n days is at most k, exactly."""

    @cache
    def go(left, run):
        if run > k:
            return 0.0
        if left == 0:
            return 1.0
        return (1 - p_lose) * go(left - 1, 0) + p_lose * go(left - 1, run + 1)

    return go(n, 0)


def median_run(n, p_lose):
    k = 0
    while longest_run_cdf(n, p_lose, k) < 0.5:
        k += 1
    return k


def test_q26():
    ma, sa = stats(1, 0.9, 8)
    mb, sb = stats(1.75, 0.4, 1)
    assert round(ma, 2) == 0.1 and round(mb, 2) == 0.1
    assert round(sa, 2) == 2.7 and round(sb, 2) == 1.35
    assert round(ma / sa, 3) == 0.037 and round(mb / sb, 3) == 0.074
    assert round(ma / sa * math.sqrt(250), 2) == 0.59 and round(mb / sb * math.sqrt(250), 2) == 1.17
    # Over 250 days.
    assert round(250 * ma, 6) == 25 and round(250 * mb, 6) == 25
    assert round(sa * math.sqrt(250), 1) == 42.7 and round(sb * math.sqrt(250), 1) == 21.3
    year = np.random.default_rng(260)
    a250 = np.where(year.random((20000, 250)) < 0.9, 1.0, -8.0).sum(axis=1)
    b250 = np.where(year.random((20000, 250)) < 0.4, 1.75, -1.0).sum(axis=1)
    assert abs(a250.mean() - 25) < 0.7 and abs(b250.mean() - 25) < 0.35
    assert abs(a250.std() - 42.7) < 0.6 and abs(b250.std() - 21.3) < 0.3
    assert median_run(250, 0.1) == 2
    assert median_run(250, 0.6) == 9
    rng = np.random.default_rng(26)
    lose = rng.random((4000, 250)) < 0.6
    runs = []
    for row in lose:
        best = cur = 0
        for x in row:
            cur = cur + 1 if x else 0
            best = max(best, cur)
        runs.append(best)
    assert abs(np.median(runs) - 9) <= 1
    a = np.where(rng.random(1_000_000) < 0.9, 1.0, -8.0)
    b = np.where(rng.random(1_000_000) < 0.4, 1.75, -1.0)
    assert abs(a.mean() - 0.1) < 0.01 and abs(b.mean() - 0.1) < 0.005
