"""Numbers gate for Book 18, chapter 29: every number in the six mock interviews and their solutions."""
import math
import pathlib
import random
import sys
from fractions import Fraction

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_mock import (
    MONTHLY,
    LRUCache,
    bloom_bits,
    bs_call,
    digital_by_spread,
    forward,
    forward_discrete_dividend,
    heads_market,
    ic_t_stat,
    kelly_even_money,
    net_sharpe,
    prob_hit_drawdown,
    psi,
    sharpe_and_drawdown,
    token_bucket,
    token_bucket_queue,
    vega,
)


def test_interview_1_trader():
    assert 0.15 * 64_000 == 9_600
    fair, sd = heads_market(3, 5)
    assert fair == 10.5 and round(sd, 2) == 1.94
    assert kelly_even_money(Fraction(10, 16)) == Fraction(1, 4) and 400 * Fraction(1, 4) == 100
    assert math.isclose(0.625 * math.log(1.25) + 0.375 * math.log(0.75), 0.0316, abs_tol=5e-5)


def test_interview_2_researcher():
    assert ic_t_stat(0.02, 2500) == 1.0
    assert 500 * 10 * 252 == 1_260_000 and 10 * 252 == 2520


def test_interview_3_developer():
    c = LRUCache(2)
    c.put("A", 1)
    c.put("B", 2)
    assert c.get("A") == 1
    c.put("C", 3)  # evicts B, the least recently used
    assert c.get("B") is None and c.get("A") == 1 and c.get("C") == 3
    for s in range(200):  # against a list-based model
        r = random.Random(s)
        cap = r.randint(1, 4)
        c, model = LRUCache(cap), []
        for _ in range(60):
            k = r.randint(0, 6)
            if r.random() < 0.5:
                got = c.get(k)
                want = next((v for kk, v in model if kk == k), None)
                assert got == want
                if want is not None:
                    model = [x for x in model if x[0] != k] + [(k, want)]
            else:
                v = r.randint(0, 99)
                c.put(k, v)
                model = [x for x in model if x[0] != k] + [(k, v)]
                model = model[-cap:]
    sent = token_bucket([0.0] * 50 + [0.5 + 0.01 * i for i in range(100)], 100, 20)
    assert len(sent) == 120 and sum(t == 0.0 for t in sent) == 20


def test_interview_4_mle():
    assert 0.99 * 1 == 0.99  # all-negative classifier's accuracy with 1% positives
    assert round(psi([0.25] * 4, [0.1, 0.2, 0.3, 0.4]), 3) == 0.228


def test_interview_5_bank():
    assert round(forward(100, 0.03, 0.01, 2), 2) == 104.08
    assert round(vega(100, 100, 0.2, 1) / 100, 3) == 0.397
    assert round(bs_call(100, 100, 0.2, 1), 2) == 7.97  # about 8, and 8 / 20 = 0.40 per point
    d = digital_by_spread(100, 100, 0.2, 1, 1)
    assert round(d, 4) == 0.4602 and abs(d - 0.460172) < 1e-4
    assert round(bs_call(100, 99, 0.2, 1) - bs_call(100, 101, 0.2, 1), 4) == round(2 * d, 4)
    for h in (4, 2, 1):  # the error falls like h^2
        assert abs(digital_by_spread(100, 100, 0.2, 1, h) - 0.460172) < 5e-4 * h * h


def test_interview_6_pm():
    sr, dd = sharpe_and_drawdown(MONTHLY)
    assert round(sr, 2) == 1.05 and round(100 * dd, 1) == -2.4
    assert len(MONTHLY) == 24
    assert round(math.sqrt((1 + sr * sr / 2) / 2), 1) == 0.9  # standard error of the Sharpe ratio, two years
    assert round(net_sharpe(1.2, 0.08, 20, 5), 3) == 1.075
    assert round(net_sharpe(1.2, 0.08, 20, 5 * math.sqrt(10)), 2) == 0.80
    p = prob_hit_drawdown(0.10, 0.10, 0.075, 1.0)
    assert round(p, 2) == 0.17
    rng = np.random.default_rng(29)
    n, steps = 20_000, 252
    dt = 1 / steps
    x = np.cumsum(0.10 * dt + 0.10 * math.sqrt(dt) * rng.standard_normal((n, steps)), axis=1)
    assert abs((x.min(axis=1) <= -0.075).mean() - p) < 0.02  # discrete monitoring slightly below
    peak = np.maximum.accumulate(np.maximum(x, 0.0), axis=1)
    assert abs(((x - peak).min(axis=1) <= -0.075).mean() - 0.53) < 0.03  # from the running peak: one in two




def test_follow_ups():
    from scipy.stats import norm

    # trader
    assert 9_600 * 7 // 100 == 672 and 9_600 - 672 == 8_928 and 9_000 * 93 // 100 + 600 * 93 // 100 == 8_928
    fair, sd = heads_market(4, 6)
    assert fair == 11 and round(sd, 2) == 1.87 and round(math.sqrt(3.5), 2) == 1.87
    assert 400 * kelly_even_money(Fraction(55, 100)) == 40 and 400 * kelly_even_money(Fraction(70, 100)) == 160

    def growth(p, f):
        return p * math.log(1 + f) + (1 - p) * math.log(1 - f)

    assert round(100 * growth(0.55, 0.25), 1) == -0.7
    assert round(100 * growth(0.70, 0.10), 1) == 3.5 and round(100 * growth(0.70, 0.40), 1) == 8.2
    # the candidate who was not hired
    assert heads_market(4, 6)[0] == 11 and round(heads_market(3, 5)[1], 2) == 1.94 and 4 / heads_market(3, 5)[1] > 2
    assert round(0.625 * math.log(1.75) + 0.375 * math.log(0.25), 2) == -0.17
    # researcher
    rho = 0.5
    assert (1 + rho) / (1 - rho) == 3 and round(1 / math.sqrt(3), 2) == 0.58
    p = 2 * (1 - norm.cdf(2.2))
    assert round(p, 3) == 0.028 and round(5 * p, 2) == 0.14
    # developer
    m, k = bloom_bits(10**7, 0.01)
    assert round(m / 1e6) == 96 and round(m / 8 / 1e6) == 12 and round(k, 1) == 6.6 and math.ceil(k) == 7
    assert round(-math.log(0.01), 1) == 4.6 and round(math.log(2) ** 2, 2) == 0.48 and 10**7 * 0.01 == 100_000
    arrivals = [0.0] * 50 + [0.5 + 0.01 * i for i in range(100)]
    out = token_bucket_queue(arrivals, 100, 20)
    waits = [d - a for d, a in zip(out, arrivals, strict=True)]
    assert len(out) == 150 and sum(w > 1e-9 for w in waits) == 30
    assert round(max(out[:50]), 6) == 0.3 and max(waits[50:]) < 1e-9
    # machine-learning engineer
    assert (5 - 2) // 1 == 3
    tp, fp = 80, 0.05 * 9_900
    assert fp == 495 and tp + fp == 575 and round(100 * tp / (tp + fp)) == 14 and round(fp / tp) == 6
    # bank quant
    assert round(2 * math.exp(-0.015), 2) == 1.97
    assert round(forward_discrete_dividend(100, 0.03, 2, 0.5, 2), 2) == 104.09
    assert round(vega(100, 100, 0.2, 0.25) / 100, 2) == 0.20
    assert 1_000_000 // 2 == 500_000
    # portfolio-manager hire
    best = max(MONTHLY)
    rest = list(MONTHLY)
    rest.remove(best)
    sr_all, dd_all = sharpe_and_drawdown(MONTHLY)
    sr_rest, dd_rest = sharpe_and_drawdown(rest)
    assert best == 2.1 and round(sr_rest, 2) == 0.86 and abs(dd_rest - dd_all) < 1e-12
    root_m = 9.6 - 4.0
    assert round(root_m, 1) == 5.6 and round(root_m**2) == 31
    assert round(net_sharpe(1.2, 0.08, 20, 5 * root_m), 2) == 0.5
    p2 = prob_hit_drawdown(0.20, 0.10, 0.075, 1.0)
    assert round(norm.cdf(-2.75), 3) == 0.003 and round(math.exp(-3) * norm.cdf(1.25), 3) == 0.045 and round(p2, 2) == 0.05
