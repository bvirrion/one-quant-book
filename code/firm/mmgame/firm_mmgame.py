"""A market-making game engine (build of Book 2, Chapter 30).

The contract pays the sum of K cards dealt face down from a 52-card deck (values 1 to 13). Each round
one trader arrives: with probability `informed` it knows the sum and buys above the ask or sells
below the bid, otherwise it passes; otherwise it is uninformed and trades, on a random side, with a
probability that falls with the width, exp(-width / patience). The maker quotes its current
expected value plus and minus half the width, and, if it updates, revises its beliefs about the sum
by Bayes' rule after each trade or pass.
"""
import math
import random
from dataclasses import dataclass


def card_sum_distribution(k: int, copies: int = 4, values: range = range(1, 14)) -> dict[int, float]:
    """Exact distribution of the sum of k cards drawn without replacement from the deck."""
    ways: dict[tuple[int, int], int] = {(0, 0): 1}                      # (cards, sum) -> count
    for v in values:
        nxt: dict[tuple[int, int], int] = {}
        for (n, s), w in ways.items():
            for j in range(min(copies, k - n) + 1):
                key = (n + j, s + j * v)
                nxt[key] = nxt.get(key, 0) + w * math.comb(copies, j)
        ways = nxt
    total = sum(w for (n, _), w in ways.items() if n == k)
    return {s: w / total for (n, s), w in sorted(ways.items()) if n == k}


@dataclass(frozen=True)
class Table:
    cards: int = 5
    rounds: int = 20
    informed: float = 0.2              # share of arriving traders who know the sum
    patience: float = 8.0              # uninformed traders' tolerance for width


def mean(post: dict[int, float]) -> float:
    return sum(s * p for s, p in post.items())


def update(post: dict[int, float], action: str, bid: float, ask: float, t: Table, width: float) -> dict[int, float]:
    """Posterior over the sum after observing `action` ('buy', 'sell' or 'pass') at these quotes."""
    q = math.exp(-width / t.patience)
    lik = {"buy": lambda s: t.informed * (s > ask) + (1 - t.informed) * q / 2,
           "sell": lambda s: t.informed * (s < bid) + (1 - t.informed) * q / 2,
           "pass": lambda s: t.informed * (bid <= s <= ask) + (1 - t.informed) * (1 - q)}[action]
    new = {s: p * lik(s) for s, p in post.items()}
    z = sum(new.values())
    return {s: p / z for s, p in new.items()} if z > 0 else post


def deal(t: Table, rng: random.Random, prior: dict[int, float]) -> tuple[int, list[tuple[float, float, float]]]:
    """The sum and, for each round, the uniforms that decide who arrives, whether an uninformed
    trader trades and on which side; dealing once lets every width face the same table."""
    value = rng.choices(list(prior), list(prior.values()))[0]
    return value, [(rng.random(), rng.random(), rng.random()) for _ in range(t.rounds)]


def play(width: float, t: Table, value: int, draws: list[tuple[float, float, float]], learn: bool = True,
         prior: dict[int, float] | None = None) -> tuple[float, list[float]]:
    """One game: (maker's P&L, the maker's mid before each round and at the end)."""
    prior = prior or card_sum_distribution(t.cards)
    post, pnl, mids = dict(prior), 0.0, []
    q = math.exp(-width / t.patience)
    for u_who, u_trade, u_side in draws:
        m = mean(post)
        mids.append(m)
        bid, ask = m - width / 2, m + width / 2
        if u_who < t.informed:
            action = "buy" if value > ask else "sell" if value < bid else "pass"
        else:
            action = ("buy" if u_side < 0.5 else "sell") if u_trade < q else "pass"
        if action == "buy":
            pnl += ask - value
        elif action == "sell":
            pnl += value - bid
        if learn:
            post = update(post, action, bid, ask, t, width)
    mids.append(mean(post))
    return pnl, mids


def expected_pnl(widths: list[float], t: Table, games: int, seed: int,
                 learn: bool = True) -> list[tuple[float, float, float]]:
    """(width, mean P&L per game, standard error) for each width, every width facing the same
    seeded deals."""
    rng, prior = random.Random(seed), card_sum_distribution(t.cards)
    deals = [deal(t, rng, prior) for _ in range(games)]
    out = []
    for w in widths:
        xs = [play(w, t, v, d, learn, prior)[0] for v, d in deals]
        m = sum(xs) / games
        sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (games - 1))
        out.append((w, m, sd / math.sqrt(games)))
    return out
