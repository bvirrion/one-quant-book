import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_searcher as fs  # noqa: E402


def test_optimal_arb():
    x, y, p = 1000.0, 3_100_000.0, 3000.0
    d, dx, prof = fs.optimal_arb(x, y, p, 0.003)
    assert d == "sell_A" and prof > 0
    g = 0.997
    # at the optimum the marginal output of the last unit sold, g x y / (x + g dx)^2, equals p
    assert math.isclose(g * x * y / (x + g * dx) ** 2, p, rel_tol=1e-9)
    for eps in (-0.01, 0.01):                          # a neighbouring size earns less
        d2 = dx * (1 + eps)
        o2 = g * d2 * y / (x + g * d2)
        assert o2 - p * d2 < prof
    assert fs.optimal_arb(1000.0, 3_000_000.0, 3000.0)[0] == "none"
    assert abs(fs.arb_exact(1000 * 10**6, 3_100_000 * 10**6, 3000.0) - prof * 10**6) < 10**4


def test_auction():
    one, two, ten = fs.auction(100.0, 1), fs.auction(100.0, 2), fs.auction(100.0, 10)
    assert one["builder"] == 0.0 and two["share"] < ten["share"] < 1.0
    assert math.isclose(two["builder"] + two["searcher"], 80 + 20 * 2 / 3, rel_tol=0.01)


def test_pool_lvr():
    ch = fs.Chain(seed=5, blocks=7200 * 3)
    r = fs.run_pool(ch)
    theory = fs.lvr_rate(0.04, 20e6) * r["days"]
    assert 0.6 * theory < r["lvr"] < 1.4 * theory
    assert math.isclose(r["hedged_pnl"], r["noise_pnl"] + r["arb_fees"] - r["arb_take"])
    assert fs.liquidation_value(1e6, 0.05, 20.0) == 49980.0 and fs.gas_cost() > 0
