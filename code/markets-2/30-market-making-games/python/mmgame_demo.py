"""Chapter 30 of Book 2: market-making games. The card-sum market (the sum of five cards dealt face
down) quoted by a maker who updates by Bayes' rule, against a table where a share of traders knows
the sum and the rest trade less the wider the quotes. All parameters are this chapter's."""
import math
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/mmgame"))
from firm_mmgame import Table, card_sum_distribution, deal, expected_pnl, mean, play, update

TABLE = Table(cards=5, rounds=20, informed=0.2, patience=8.0)
FINE = [w / 2 for w in range(16, 31)]                  # 8 to 15 points, in half points
COARSE = [float(w) for w in range(0, 31, 2)]


def distribution() -> list[tuple[int, float]]:
    return sorted(card_sum_distribution(TABLE.cards).items())


def first_trade() -> dict[str, float]:
    """The maker's first quote at width 10 and its revised mid after a buy, a sell and a pass."""
    prior = card_sum_distribution(TABLE.cards)
    m = mean(prior)
    sd = math.sqrt(sum((s - m) ** 2 * p for s, p in prior.items()))
    bid, ask = m - 5, m + 5
    return {"mean": m, "sd": sd, "bid": bid, "ask": ask,
            "after_buy": mean(update(prior, "buy", bid, ask, TABLE, 10.0)),
            "after_sell": mean(update(prior, "sell", bid, ask, TABLE, 10.0)),
            "after_pass": mean(update(prior, "pass", bid, ask, TABLE, 10.0)),
            "p_informed_given_buy": TABLE.informed * sum(p for s, p in prior.items() if s > ask)
            / (TABLE.informed * sum(p for s, p in prior.items() if s > ask)
               + (1 - TABLE.informed) * math.exp(-10 / TABLE.patience) / 2)}


def one_game(width: float = 11.5, seed: int = 7) -> tuple[int, list[float], float]:
    prior = card_sum_distribution(TABLE.cards)
    value, draws = deal(TABLE, random.Random(seed), prior)
    pnl, mids = play(width, TABLE, value, draws, True, prior)
    return value, mids, pnl


def curves(games: int = 600, seed: int = 30) -> dict[str, list[tuple[float, float, float]]]:
    out = {}
    for pi in (0.1, 0.2, 0.3):
        t = Table(TABLE.cards, TABLE.rounds, pi, TABLE.patience)
        out[f"learn{int(100 * pi)}"] = expected_pnl(COARSE, t, games, seed)
    out["naive20"] = expected_pnl(COARSE, TABLE, games, seed, learn=False)
    return out


def problem(games: int = 2000, seed: int = 30) -> dict[str, float]:
    learn = expected_pnl(FINE, TABLE, games, seed)
    naive = expected_pnl(FINE, TABLE, games, seed, learn=False)
    best, best_naive = max(learn, key=lambda x: x[1]), max(naive, key=lambda x: x[1])
    at = {w: (m, se) for w, m, se in learn}
    none = Table(TABLE.cards, TABLE.rounds, 0.0, TABLE.patience)
    return {"width": best[0], "pnl": best[1], "se": best[2], "width_naive": best_naive[0],
            "pnl_naive": best_naive[1], "pnl_8": at[8.0][0], "pnl_15": at[15.0][0],
            "no_informed_8": expected_pnl([8.0], none, games, seed)[0][1],
            "trade_prob": math.exp(-best[0] / TABLE.patience)}
