import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_agentmkt import (  # noqa: E402
    FACTS,
    SEC,
    T0,
    MarketMaker,
    Metaorder,
    Population,
    PopulationConfig,
    distance,
    facts,
    msm,
    session,
)

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tape"))
from firm_tape import TapeConfig, simulate  # noqa: E402


def test_population_is_deterministic_and_exogenous_flow_is_shared():
    cfg = PopulationConfig(lo_rate=3.0, near=0.3, cancel=0.05, depth=10)
    a, _ = session(cfg, 300.0, 5)
    b, _ = session(cfg, 300.0, 5)
    assert a.tape().trades["qty"].sum() == b.tape().trades["qty"].sum() > 0
    # the noise orders and the jumps of V do not depend on what else happens
    p1, p2 = Population(cfg, 5, 300.0), Population(cfg, 5, 300.0)
    assert p1.exo == p2.exo and len(p1.exo) > 200
    long = Population(PopulationConfig(run_tail=1.5), 5, 300.0)
    signs = [x for _, k, x in long.exo if k == "noise"]
    same = sum((u > 0) == (v > 0) for u, v in zip(signs, signs[1:], strict=False)) / (len(signs) - 1)
    assert same > 0.6                                           # runs of Pareto length: signs persist


def test_metaorder_trades_its_plan():
    cfg = PopulationConfig(lo_rate=3.0, near=0.3, cancel=0.05, depth=10)
    res, _ = session(cfg, 400.0, 2, agents=[Metaorder([(T0 + 100 * SEC, 1, 3000, 10, 100 * SEC)])])
    fills = res.agents["meta"].fills
    assert sum(f[5] for f in fills) == 3000 and all(f[3] > 0 for f in fills)


def test_activity_curve_shapes_the_flow():
    cfg = PopulationConfig(lo_rate=3.0, near=0.3, cancel=0.05, depth=10, curve=(3.0, 1.0, 1.0, 3.0))
    p = Population(cfg, 5, 400.0)
    t = [t for t, k, _ in p.exo if k == "noise"]
    first, second = sum(x < 100 for x in t), sum(100 <= x < 200 for x in t)
    assert first > 2 * second > 0                                # three times the rate in the first quarter
    assert Population(PopulationConfig(), 5, 300.0).exo == Population(PopulationConfig(curve=()), 5, 300.0).exo


def test_market_maker_quotes_and_bounds_its_inventory():
    cfg = PopulationConfig(lo_rate=2.0, near=0.5, cancel=0.02, depth=10, noise=0.9, fund=0.2)
    res, _ = session(cfg, 600.0, 3, agents=[MarketMaker(skew=0.1, max_lots=5)])
    mm = res.agents["mm"]
    pos = [0]
    for f in mm.fills:
        pos.append(pos[-1] + f[3] * f[5])
    assert len(mm.fills) > 20 and max(abs(p) for p in pos) <= 500 + 200    # max_lots plus one quote in flight
    assert all(f[6] == "A" for f in mm.fills)                              # it only ever rests


def test_facts_count_one_sign_per_aggressive_order_and_msm_finds_the_minimum():
    f = facts(simulate(TapeConfig(seed=3, news_at=None)), 30.0)
    assert set(f) == set(FACTS) and 1.0 <= f["spread"] < 1.5 and 0 < f["sign_acf1"] < 0.5 and f["depth"] > 1
    target, scale = {"a": 1.0, "b": 2.0}, {"a": 1.0, "b": 0.5}
    assert distance({"a": 2.0, "b": 2.5}, target, scale) == 2.0
    out = msm(lambda p, s: {"a": p[0] + 0.01 * s, "b": p[1]}, [(0, 0), (1, 2), (2, 2)], target, scale, (1, 2))
    assert out["best"] == (1, 2) and abs(out["distance"] - 0.015**2) < 1e-12 and len(out["all"]) == 3
