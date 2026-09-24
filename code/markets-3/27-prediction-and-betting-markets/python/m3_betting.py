"""Book 3, Chapter 27: removing a bookmaker's margin four ways, a favourite--longshot bias measured on a
synthetic book of results, and the election-night gap between two venues' contracts on one event."""
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/odds"))
from firm_odds import additive, kelly, multiplicative, overround, power, shin  # noqa: E402

BOOK = [1.5, 4.0, 7.0]


def methods(odds: list[float] = BOOK) -> dict[str, list[float]]:
    return {"multiplicative": multiplicative(odds), "additive": additive(odds), "power": power(odds),
            "shin": shin(odds)[0]}


def biased_odds(p: list[float], alpha: float = 0.92, margin: float = 0.10) -> list[float]:
    """A bookmaker who prices implied probabilities proportional to p^alpha (alpha < 1 overprices
    longshots), grossed up by the margin."""
    w = [x**alpha for x in p]
    s = sum(w)
    return [1 / ((1 + margin) * x / s) for x in w]


def flb_book(n_events: int = 20_000, runners: int = 8, seed: int = 27) -> list[tuple[float, float]]:
    """Synthetic races: true win probabilities from a Dirichlet-like draw; one unit staked on every runner.
    Returns (decimal odds, realised return per unit) for every bet."""
    rng = random.Random(seed)
    out = []
    for _ in range(n_events):
        w = [rng.expovariate(1.0) ** 1.5 for _ in range(runners)]
        s = sum(w)
        p = [x / s for x in w]
        odds = biased_odds(p)
        u, acc, winner = rng.random(), 0.0, runners - 1
        for i, x in enumerate(p):
            acc += x
            if u < acc:
                winner = i
                break
        out += [(o, (o - 1) if i == winner else -1.0) for i, o in enumerate(odds)]
    return out


def returns_by_odds(bets: list[tuple[float, float]],
                    edges=(1, 2, 3, 5, 10, 20, 50, 1_000)) -> list[tuple[str, float, int]]:
    """Mean realised return per unit staked, by decimal-odds bucket."""
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        r = [x for o, x in bets if lo <= o < hi]
        rows.append((f"{lo}-{hi}", sum(r) / len(r) if r else float("nan"), len(r)))
    return rows


def election_gap(yes_a: float = 0.58, yes_b: float = 0.62, fee_a: float = 0.01, fee_b: float = 0.005,
                 days: int = 30, rate: float = 0.045) -> dict:
    """Buy YES on venue A and NO on venue B (price 1 - yes_b): one contract of each pays exactly 1. Fees per
    contract; the capital is locked until resolution at the stated money-market rate."""
    cost = yes_a + (1 - yes_b) + fee_a + fee_b
    carry = cost * rate * days / 365
    return {"cost": cost, "profit": 1 - cost - carry, "gap": yes_b - yes_a,
            "breakeven_gap": fee_a + fee_b + carry}


def kelly_stake(belief: float = 0.65, price: float = 0.58) -> float:
    """Kelly fraction for a contract bought at `price` paying 1, i.e. decimal odds 1 / price."""
    return kelly(belief, 1 / price)


__all__ = ["methods", "overround", "flb_book", "returns_by_odds", "election_gap", "kelly_stake"]
