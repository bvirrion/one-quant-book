"""Numbers gate: every numerical answer printed in Book 5, Chapter 6 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_american import (
    accuracy_table,
    bermudan_put,
    dividend_threshold,
    hook,
    perpetual_put,
    perpetual_put_value,
    premium_vs_rate,
    put_boundary,
    results,
)

H, R = hook(), results()


def test_text():
    assert (round(H["exercise"], 2), round(H["hold"], 2), round(H["loss_per_share"], 2)) == (20.30, 19.56, 0.74)
    prem = dict((round(100 * r), p) for r, _, p in premium_vs_rate([0.0, 0.05, 0.10]))
    assert (round(prem[0], 2), round(prem[5], 2), round(prem[10], 2)) == (0.0, 0.52, 1.06)
    assert round(perpetual_put(100, 0.05, 0.2)[0], 2) == 71.43 and round(R["boundary_1y"], 2) == 81.11
    three = put_boundary(100.0, 3.0, 0.05, 0.0, 0.20, n=3000)
    assert round(three[0][1], 1) == 76.2
    assert (round(H["interest"], 3), round(H["d_star"], 3)) == (0.254, 0.255)
    assert round(100 * (H["d_star"] - H["interest"]), 1) == 0.1
    rows = {(r["spot"], r["r"], r["q"]): r for r in accuracy_table() if r["right"] == "P"}
    for key, eu, tr, qa, err in [((100, 0.05, 0.0), 5.5735, 6.0902, 6.0976, 0.0074),
                                 ((90, 0.08, 0.0), 11.2671, 12.1792, 12.1151, -0.0641),
                                 ((110, 0.03, 0.0), 1.5070, 1.5201, 1.5229, 0.0028),
                                 ((100, 0.05, 0.04), 9.0396, 9.2168, 9.2444, 0.0277)]:
        r = rows[key]
        assert (round(r["european"], 4), round(r["tree"], 4), round(r["baw"], 4), round(r["err"], 4)) == (eu, tr, qa, err)
    assert all(abs(r["err"]) < 0.03 for k, r in rows.items() if k != (90, 0.08, 0.0))
    b12 = bermudan_put(100.0, 100.0, 1.0, 0.05, 0.20, 12)
    assert round(b12, 2) == 6.04 and round((b12 - 5.5735) / (6.0902 - 5.5735), 1) == 0.9


def test_exercises():
    assert (round(R["premium"], 4), round(100 * R["premium"] / R["european"], 1)) == (0.5167, 9.3)
    assert round(perpetual_put_value(100, 100, 0.05, 0.2), 2) == 12.32
    assert round(50 * (1 - math.exp(-0.05 * 60 / 365)), 2) == 0.41
    assert (round(dividend_threshold(100.30, 80, 90 / 365, 0.04, 0.25), 3), round(80 * (1 - math.exp(-0.04 * 90 / 365)), 3)) == (0.932, 0.785)
    from firm_bs import implied_vol
    assert round(100 * implied_vol(6.0902, 100 * math.exp(0.05), 100, 1, math.exp(-0.05), "P"), 1) == 21.4


def test_problem():
    assert round(H["transfer_usd_all"], -2) == 744_600 and round(H["transfer_usd"], -3) == 335_000
    assert round(1.00 + 99.30 - H["hold"] - 80.0, 2) == 0.74
