import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_posisig import forward, hedging_market, ic, published, zscore  # noqa: E402


def test_published_schedule():
    x = np.arange(12.0)[:, None]
    p = published(x, 5, 1, 3)[:, 0]
    # reports on days 1, 6, 11 known on days 4, 9, 14
    assert np.isnan(p[:4]).all() and p[4:9].tolist() == [1.0] * 5 and p[9:12].tolist() == [6.0] * 3
    assert published(x, 5, 1, 0)[1, 0] == 1.0


def test_forward_ic_zscore():
    r = np.arange(10.0)[:, None] * np.ones((1, 3))
    f = forward(r, 2)
    assert f[0, 0] == 1 + 2 and np.isnan(f[-1, 0])
    rng = np.random.default_rng(2)
    s = rng.standard_normal((200, 8))
    m, t = ic(s, s + 0.3 * rng.standard_normal((200, 8)), 1)
    m5, t5 = ic(s, s + 0.3 * rng.standard_normal((200, 8)), 1, 5)
    assert 0.8 < m < 1.0 and t > 20 and t5 < t / 2
    z = zscore(np.array([0.0, 1.0, 0.0, 1.0, 5.0])[:, None], 4)
    assert math.isclose(z[4, 0], (5 - 0.5) / np.std([0, 1, 0, 1], ddof=1))


def test_hedging_premium_is_planted():
    rng = np.random.default_rng(0)
    r = 0.01 * rng.standard_normal((20000, 5))
    M = hedging_market(r, np.full(5, 0.16), 20.0, 1.0, 0.0, 0.0, np.random.default_rng(1))
    extra = M["r"][1:] - r[1:]
    assert np.allclose(extra, 0.16 * M["hedge"][:-1] / 252) and np.allclose(M["spec"], M["hedge"])
