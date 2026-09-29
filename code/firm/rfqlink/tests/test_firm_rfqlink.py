import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_rfqlink as rl  # noqa: E402

FAST = rl.Pipeline((rl.Stage("all", 1.0, 0.0),))


def test_matches_rfqmm_when_everyone_answers():
    a = rl.auction(5, FAST, FAST, "expiry", n=5000, seed=3)
    s = rl.mm.simulate(5, 15.0, n=5000, seed=3)
    assert abs(a["win"] - float(s["win"].mean())) < 1e-12 and abs(a["traded"] - float(s["traded"].mean())) < 1e-12


def test_response_and_miss():
    p = rl.Pipeline((rl.Stage("a", 10.0, 0.0), rl.Stage("b", 5.0, 0.0)))
    assert np.allclose(rl.response_ms(p, 4, np.random.default_rng(0)), 15.0)
    assert rl.miss_prob(p, 14.0, n=100) == 1.0 and rl.miss_prob(p, 16.0, n=100) == 0.0
    m = rl.Pipeline(p.stages, manual_share=1.0, manual_median_ms=5000.0, manual_sigma=0.0)
    assert rl.miss_prob(m, 2000.0, n=100) == 1.0


def test_rules():
    slow = rl.scaled(FAST, 50.0)
    e = rl.auction(5, slow, FAST, "expiry", n=4000)
    f = rl.auction(5, slow, FAST, "first_ok", n=4000)
    k = rl.auction(5, slow, FAST, "first_k", k=4, n=4000)
    assert f["win"] < e["win"] / 5 and f["lost_to_speed"] > 0 and e["lost_to_speed"] == 0.0
    assert k["win"] == 0.0 and e["win"] > 0.15
    assert rl.log_grid(1, 100, 2) == [1, 10 ** 0.5, 10, 10 ** 1.5, 100]
