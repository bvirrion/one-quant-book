"""Book 3, Chapter 21: stale quotes picked off under two in-block orderings, and the loss of a vault that
inherits a liquidated position in a thin market that is then squeezed."""
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/blockbook"))
from firm_blockbook import Action, Book, run_block  # noqa: E402


def replay(rule: str, blocks: int = 1_000, seed: int = 21, p_taker_first: float = 0.5) -> list[tuple[int, int, float]]:
    """A maker quotes 5 lots two ticks either side of fair value with post-only orders and, every block,
    cancels and requotes around the new fair value. When fair value jumps past a resting quote, a taker
    sends an IOC to pick it off. Within a block the taker's order arrives before the maker's cancel with
    probability p_taker_first. Returns (block, lots picked off so far, maker's cumulative loss in ticks)."""
    rng = random.Random(seed)
    book, fair, oid = Book(), 1_000, 1
    run_block(book, [Action("alo", "M", "sell", fair + 2, 5, 1), Action("alo", "M", "buy", fair - 2, 5, 2)], "arrival")
    live = {1: ("sell", fair + 2), 2: ("buy", fair - 2)}
    picked, loss, rows = 0, 0.0, []
    for blk in range(1, blocks + 1):
        fair += round(rng.gauss(0, 2.0))
        maker = [Action("cancel", "M", oid=o) for o in live]
        new = {oid + 1: ("sell", fair + 2), oid + 2: ("buy", fair - 2)}
        maker += [Action("alo", "M", s, p, 5, o) for o, (s, p) in new.items()]
        oid += 2
        taker = []
        for s, p in live.values():
            if s == "sell" and p < fair:
                taker.append(Action("ioc", "T", "buy", p, 5))
            if s == "buy" and p > fair:
                taker.append(Action("ioc", "T", "sell", p, 5))
        acts = taker + maker if rng.random() < p_taker_first else maker + taker
        for f in run_block(book, acts, rule):
            if f.maker == "M":
                picked += f.qty
                loss += f.qty * abs(fair - f.price)
        live = {o: sp for o, sp in new.items() if any(q[1] == o for q in book.bids + book.asks)}
        rows.append((blk, picked, loss))
    return rows


def squeeze_loss(notional: float, squeeze: float, buffer: float) -> float:
    """Loss of a vault that takes over a short of this notional with `buffer` of it left as margin, when the
    price then rises by `squeeze` (1.0 = +100%) before it can close."""
    return max(0.0, notional * (squeeze - buffer))


def oi_cap_for(max_loss: float, squeeze: float, buffer: float) -> float:
    """Largest position (notional) whose takeover keeps the vault's loss within max_loss at that squeeze."""
    return max_loss / (squeeze - buffer)


BUFFER_3X = 2 / 3 * 1 / 6          # backstop at 2/3 of a maintenance margin of 1/6 (half of 1/3 at 3x)
