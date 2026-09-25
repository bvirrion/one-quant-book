import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_newsevent import NewsConfig, immediate_share, remaining, simulate_news  # noqa: E402


def test_stream():
    items = simulate_news(500, 1000, NewsConfig(), np.random.default_rng(0))
    assert abs(len(items) / 500 - 40) < 3 and np.all(items["attention"] <= 1.0)
    assert abs(items["halted"].mean() - 2 * (1 - 0.9938)) < 0.005          # |tone| > 2.5 standard deviations


def test_remaining_by_hand():
    cfg = NewsConfig(tau=0.2, floor=0.5)
    it = np.zeros(2, dtype=[("attention", float), ("halted", bool)])
    it["attention"], it["halted"] = [1.0, 0.0], [False, True]
    assert np.allclose(immediate_share(it["attention"], cfg), [1.0, 0.5])
    assert np.allclose(remaining(it, 0.2, cfg), [math.exp(-1), 0.5])
    assert np.allclose(remaining(it, None, cfg), [0.0, 0.5])
