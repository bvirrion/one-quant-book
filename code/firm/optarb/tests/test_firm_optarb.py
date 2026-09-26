import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_optarb as oa  # noqa: E402


def test_box_and_jelly():
    assert math.isclose(oa.box_rate(95, 105, 10 * math.exp(-0.04 * 0.25), 0.25), 0.04)
    lend, borrow = oa.box_edge(9.89, 9.87, 95, 105, 0.25, 0.04)
    assert math.isclose(lend, 10 * math.exp(-0.01) - 9.89) and borrow < 0
    a, b = oa.Listings(), oa.Listings(years=0.5)
    carry = oa.jelly_roll(a.fair[(100, "C")], a.fair[(100, "P")], b.fair[(100, "C")], b.fair[(100, "P")], 100, 0.25, 0.5, 0.04)
    assert abs(carry - 0.04) < 1e-9


def test_scan():
    one = oa.scan(oa.Listings(n_venues=1, seed=2, noise=0.0), rounds=200)
    assert one["per_snapshot"] == 0.0                         # no noise, a 10-cent market: no parity violation
    many = oa.scan(oa.Listings(n_venues=6, seed=2), lag_rho=0.5, rounds=300)
    sticky = oa.scan(oa.Listings(n_venues=6, seed=2), lag_rho=0.95, rounds=300)
    assert many["per_snapshot"] > 0 and sticky["survive"] > many["survive"]


def test_dividend_curve():
    d = oa.dividend_curve([0.01, 0.05, 0.2])
    assert d[0.01]["net"] == 0.0 and 0 < d[0.05]["per_public"] < d[0.2]["per_public"]
    # break-even share of failures: cost per q equals twice the gain times the share
    c = 4 * 0.2 + 2 * 0.1
    assert oa.dividend_curve([c / 60 * 0.99])[c / 60 * 0.99]["q"] == 0.0
    assert oa.exercise_threshold() < 0.5
