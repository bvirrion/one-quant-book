"""Book 18, chapter 4: online assessments.

Scoring rules with negative marking, a time-budget plan, a finite-difference sequence solver,
the seating puzzle by exhaustive search, the pump game, and a retest model.
"""
import itertools
from fractions import Fraction
from math import erf, sqrt


def item_value(p, penalty):
    """Expected marks for answering an item correct with probability p: +1 right, -penalty wrong."""
    return p - penalty * (1 - p)


def breakeven_confidence(penalty):
    """Answer only when p exceeds penalty / (1 + penalty)."""
    return Fraction(penalty) / (1 + Fraction(penalty))


def plan_score(n_easy, t_easy, p_easy, t_hard, p_hard, total_seconds, penalty):
    """Expected score when all easy items are done first, then hard ones while time remains,
    attempting hard items only when they have positive value. Returns (hard attempted, score)."""
    left = total_seconds - n_easy * t_easy
    n_hard = int(left // t_hard) if item_value(p_hard, penalty) > 0 else 0
    return n_hard, n_easy * item_value(p_easy, penalty) + n_hard * item_value(p_hard, penalty)


def next_by_differences(seq):
    """Extend a sequence whose k-th differences are eventually constant."""
    rows = [list(seq)]
    while len(set(rows[-1])) > 1:
        r = rows[-1]
        rows.append([b - a for a, b in zip(r, r[1:], strict=False)])
        if len(rows[-1]) < 2:
            raise ValueError("not enough terms")
    nxt = rows[-1][-1]
    for r in reversed(rows[:-1]):
        nxt = r[-1] + nxt
    return nxt


def seating_solutions():
    """The chapter's seating puzzle: seats 0..4 left to right."""
    out = []
    for p in itertools.permutations("ABCDE"):
        pos = {x: i for i, x in enumerate(p)}
        if pos["C"] != 0:
            continue
        if pos["A"] in (0, 4) or abs(pos["A"] - pos["B"]) == 1:
            continue
        if pos["E"] - pos["D"] != 1:
            continue
        if pos["B"] <= pos["A"]:
            continue
        out.append("".join(p))
    return out


def pump_value(k: int, n: int) -> Fraction:
    """Balloon bursts at a uniform point in 1..n; k pumps pay k if the burst point exceeds k, else 0."""
    return Fraction(k * (n - k), n)


def pass_probability(ability: float, mark: float, noise: float, attempts: int = 1) -> float:
    """Chance that at least one of `attempts` independent sittings scores above `mark`."""
    p = 1 - 0.5 * (1 + erf((mark - ability) / (noise * sqrt(2))))
    return 1 - (1 - p) ** attempts
