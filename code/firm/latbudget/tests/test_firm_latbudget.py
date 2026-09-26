import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_latbudget as lb


def test_quantile_and_levels():
    assert lb.quantile(range(1, 101), 0.99) == 100 and lb.quantile(range(1, 101), 0.5) == 51
    assert abs(lb.stage_level(0.99, 4) - 0.9975) < 1e-12
    assert lb.allocate(1000, [1, 3]) == [250.0, 750.0]


def test_union_bound_holds_for_any_dependence():
    rng = np.random.default_rng(1)
    n = 200_000
    u = rng.random(n)
    for x, y in [(rng.exponential(1, n), rng.exponential(1, n)),            # independent
                 (-np.log(1 - u), -np.log(1 - u)),                          # comonotone
                 (-np.log(1 - u), -np.log(u))]:                             # countermonotone
        lhs = lb.quantile(x + y, 0.98)
        assert lhs <= lb.quantile(x, 0.99) + lb.quantile(y, 0.99) + 1e-9


def test_p99_is_not_subadditive():
    # each stage stalls 0.9% of the time: its own p99 is the fast value, the sum's p99 is a stall
    rng = np.random.default_rng(2)
    n = 400_000
    x = np.where(rng.random(n) < 0.009, 100.0, 1.0)
    y = np.where(rng.random(n) < 0.009, 100.0, 1.0)
    assert lb.quantile(x, 0.99) == 1.0 and lb.quantile(y, 0.99) == 1.0
    assert lb.quantile(x + y, 0.99) == 101.0


def test_budget_check():
    s = {"a": np.arange(1, 101.0), "b": np.full(100, 10.0)}
    b = lb.Budget((lb.Stage("a", {0.5: 60}), lb.Stage("b", {0.99: 5})), {0.99: 200})
    rows = b.check(s)
    assert [r["ok"] for r in rows] == [True, False, True]
    assert rows[2]["measured"] == 110.0
    assert len(lb.compose_independent(s, 1000, seed=3)) == 1000
