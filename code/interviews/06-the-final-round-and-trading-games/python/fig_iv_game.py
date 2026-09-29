"""Chart data for Book 18, chapter 6: fair value and 5-95% range of the three-card sum as cards are revealed."""
import pathlib
import random

from iv_game import DECK, fair_after, sum_distribution

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "interviews" / "06-the-final-round-and-trading-games"


def band(revealed, k=3, lo_q=0.05, hi_q=0.95):
    """Smallest sums whose cumulative probability reaches lo_q and hi_q, given the revealed cards."""
    rest = list(DECK)
    for v in revealed:
        rest.remove(v)
    need = k - len(revealed)
    if need == 0:
        s = sum(revealed)
        return s, s
    dist = sum_distribution(rest, need)
    cum, lo, hi = 0, None, None
    for s in sorted(dist):
        cum += dist[s]
        if lo is None and cum >= lo_q:
            lo = s
        if cum >= hi_q:
            hi = s
            break
    return lo + sum(revealed), hi + sum(revealed)


def game_rows(seed=7):
    cards = random.Random(seed).sample(DECK, 3)
    rows = []
    for r in range(4):
        lo, hi = band(cards[:r])
        rows.append((r, float(fair_after(cards[:r])), lo, hi))
    return cards, rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cards, rows = game_rows()
    text = ["revealed,fair,lo,hi"] + [f"{r},{f:.3f},{lo},{hi}" for r, f, lo, hi in rows]
    (OUT / "game.csv").write_text("\n".join(text) + "\n")


if __name__ == "__main__":
    main()
