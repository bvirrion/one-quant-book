"""Book 3, Chapter 26: what message loss does to a locally built order book. A true book changes by
absolute-quantity level updates; a client that loses each message with probability p either applies what
it receives (and is silently wrong until the lost level is overwritten) or detects the gap from the update
ids and resynchronises from a snapshot, which takes R messages to arrive."""
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/wsbook"))
from firm_wsbook import Book  # noqa: E402

MID = 1_000


def _event(rng: random.Random) -> tuple[list, list]:
    """One level update within ten ticks of the mid: bids below it, asks above; a fifth are deletions."""
    off = rng.randint(1, 10)
    q = 0 if rng.random() < 0.2 else rng.randint(1, 20)
    return ([(MID - off, q)], []) if rng.random() < 0.5 else ([], [(MID + off, q)])


def simulate(p: float, n: int = 200_000, resync_msgs: int = 50, seed: int = 26) -> dict:
    """Fractions of messages at which the client's top-10 book is silently wrong (no gap detection) or
    flagged stale (gap detection and resync), and the mean length of silent-error episodes."""
    rng, loss = random.Random(seed), random.Random(seed + 1)
    truth, naive, careful = Book(), Book(), Book()
    init_b = [(MID - k, 10) for k in range(1, 11)]
    init_a = [(MID + k, 10) for k in range(1, 11)]
    for b in (truth, naive, careful):
        b.snapshot(0, init_b, init_a)
    wrong = stale = episodes = 0
    resync_at = None
    in_error = False
    for i in range(1, n + 1):
        bids, asks = _event(rng)
        truth.apply(i, i, bids, asks)
        lost = loss.random() < p
        if not lost:
            naive.apply(i, i, bids, asks)
            naive.update_id = i                          # a client that ignores ids applies everything
            if careful.apply(i, i, bids, asks) == "gap" and resync_at is None:
                resync_at = i + resync_msgs
        else:
            naive.update_id = i
        if resync_at is not None and i >= resync_at:
            careful.snapshot(i, list(truth.bids.items()), list(truth.asks.items()))
            resync_at = None
        is_wrong = naive.top() != truth.top()
        wrong += is_wrong
        episodes += is_wrong and not in_error
        in_error = is_wrong
        stale += not careful.synced
    return {"silent_wrong": wrong / n, "stale": stale / n, "mean_error_msgs": wrong / episodes if episodes else 0.0}
