"""Experiments with allocation algorithms (Chapter 19): who is filled, and what each rule rewards."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/match"))
from firm_match import Resting, configurable, fifo, pro_rata

EXAMPLE = [Resting("A", 10, top=True), Resting("B", 200), Resting("C", 40, lmm=True), Resting("D", 250)]


def compare(book: list[Resting], qty: int) -> dict[str, dict[str, int]]:
    return {
        "fifo": fifo(book, qty),
        "pro_rata": pro_rata(book, qty, min_alloc=2),
        "split": configurable(book, qty, top_pct=10, lmm_pct=10, fifo_pct=40, min_alloc=2),
    }


def fill_vs_size(my_sizes: range, others: int, aggressor: int, min_alloc: int = 2) -> list[tuple[int, int]]:
    """Pro rata: what a newcomer at the back of the queue receives as a function of the size it shows."""
    out = []
    for s in my_sizes:
        book = [Resting("others", others), Resting("me", s)]
        out.append((s, pro_rata(book, aggressor, min_alloc).get("me", 0)))
    return out


def expected_fill_by_position(queue_ahead: np.ndarray, my_size: int, level: int, mean_aggressor: float,
                              n: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Expected fill of `my_size` lots in a level of `level` lots, with `queue_ahead` lots in front,
    when one aggressor of exponential size arrives: FIFO against pro rata (no minimum)."""
    rng = np.random.default_rng(seed)
    agg = np.maximum(1, rng.exponential(mean_aggressor, n).astype(int))
    f = np.array([np.clip(agg - q, 0, my_size).mean() for q in queue_ahead])
    p = np.full(len(queue_ahead), np.minimum(agg, level).mean() * my_size / level)
    return f, p
