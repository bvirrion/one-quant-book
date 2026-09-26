"""Numbers gate: every numerical answer printed in Book 10, chapter 6 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_ticks import did_panel, priority_compare, tick_experiment  # noqa: E402, I001
from firm_queuevalue import expected_time_to_fill, fill_probability, implicit_spread  # noqa: E402, I001


def r(x, d=2):
    return round(float(x), d)


def test_grids():
    g = tick_experiment()
    assert [r(g[m]["spread_cents"]) for m in (1, 2, 5, 10)] == [1.07, 2.06, 5.03, 10.03]
    assert [r(100 * g[m]["one_tick"], 1) for m in (1, 2, 5, 10)] == [94.2, 97.1, 99.4, 99.7]
    assert [r(g[m]["depth"], -1) for m in (1, 2, 5, 10)] == [1740, 3020, 6560, 10780]
    assert [r(g[m]["orders_at_best"], 1) for m in (1, 2, 5, 10)] == [8.7, 15.3, 33.6, 55.5]
    assert [r(g[m]["t_fill_median"], 1) for m in (1, 2, 5, 10)] == [11.3, 24.1, 55.7, 81.4]
    assert [r(100 * g[m]["fill_share"], 1) for m in (1, 2, 5, 10)] == [15.3, 12.3, 8.0, 5.6]
    assert [r(g[m]["eff_half_cents"]) for m in (1, 2, 5, 10)] == [0.56, 1.05, 2.53, 5.02]
    assert [r(g[m]["eta"], 3) for m in (1, 2, 5, 10)] == [0.108, 0.058, 0.019, 0.007]
    assert [r(g[m]["implicit_cents"]) for m in (1, 2, 5, 10)] == [0.22, 0.23, 0.19, 0.14]
    assert [g[m]["continuations"] for m in (1, 10)] == [353, 26] and [g[m]["alternations"] for m in (1, 10)] == [1632, 1879]
    assert [r(g[m]["trades"], 0) for m in (1, 5)] == [1392, 1544]
    # ratios quoted for the five-fold tick
    assert (r(g[5]["spread_cents"] / g[1]["spread_cents"], 1), r(g[5]["depth"] / g[1]["depth"], 1),
            r(g[5]["t_fill_median"] / g[1]["t_fill_median"], 1)) == (4.7, 3.8, 4.9)
    assert r(g[5]["eff_half_cents"] / g[1]["eff_half_cents"], 1) == 4.5


def test_queue_values():
    g = tick_experiment()
    front = [g[m]["by_orders"][0]["value"] for m in (1, 2, 5, 10)]
    back = [g[m]["by_orders"][-1]["value"] for m in (1, 2, 5, 10)]
    assert [r(x) for x in front] == [0.57, 0.66, 1.26, 2.05]
    assert [r(x, 3) for x in back] == [0.001, 0.005, 0.094, 0.188]
    assert [r(a - b) for a, b in zip(front, back, strict=True)] == [0.57, 0.66, 1.16, 1.86]
    assert r(front[2] / front[0], 1) == 2.2
    b1 = g[1]["by_orders"]
    assert [r(b["fill"]) for b in b1] == [0.54, 0.34, 0.29, 0.22, 0.15, 0.11, 0.07, 0.06]
    assert (r(b1[0]["adverse"]), r(b1[-1]["adverse"])) == (-0.71, 0.48)
    assert (r(g[1]["mu"], 3), r(g[1]["theta"], 3)) == (0.194, 0.063)
    bd = [fill_probability(b["lo"], g[1]["mu"], g[1]["theta"], g[1]["theta"]) for b in b1]
    assert (r(bd[0]), r(bd[3]), r(bd[-1])) == (0.76, 0.44, 0.13)


def test_priority():
    p = priority_compare()
    f, q = p["fifo"], p["pro_rata"]
    assert [r(b["fill"]) for b in f] == [0.70, 0.45, 0.32, 0.15, 0.05]
    assert [r(b["fill"]) for b in q] == [0.78, 0.64, 0.68, 0.66, 0.58]
    assert (r(f[0]["value"]), r(f[-1]["value"], 3), r(q[0]["value"]), r(q[-1]["value"], 3)) == (1.28, 0.081, 0.72, 0.093)
    assert (r(f[0]["value"] - f[-1]["value"]), r(q[0]["value"] - q[-1]["value"])) == (1.20, 0.63)
    assert (r(f[-1]["t_fill"], 1), r(q[-1]["t_fill"], 1)) == (76.7, 4.3)


def test_did():
    d = did_panel()
    assert d["n_obs"] == 96
    s, dp = d["spread"], d["depth"]
    assert (r(s["did"]), r(s["before_after"]), r(s["control_change"])) == (3.97, 4.01, 0.03)
    assert (r(dp["did"], -1), r(dp["before_after"], -1), r(dp["control_change"], -1)) == (7960, 7560, -400)
    assert (r(dp["se_cluster"], -1), r(dp["se_ols"], -1), r(dp["se_cluster"] / dp["se_ols"], 1)) == (2270, 1340, 1.7)
    c = dp["cells"]
    assert [r(c[k], -1) for k in ("t1p0", "t1p1", "t0p0", "t0p1")] == [2400, 9960, 2750, 2350]
    assert (r(c["t1p0"], 1), r(c["t1p0"] + c["t0p1"] - c["t0p0"], 1)) == (2402.8, 1998.8)      # the figure's dashed line


def test_exercises():
    # 1: relative tick of one cent at 4 and 400 dollars, in basis points
    assert (r(0.01 / 4 * 1e4, 1), r(0.01 / 400 * 1e4, 2)) == (25.0, 0.25)
    # 2: 40 continuations, 160 alternations
    eta = 40 / (2 * 160)
    assert (eta, implicit_spread(eta, 1.0)) == (0.125, 0.25)
    # 3: two orders ahead
    assert r(fill_probability(2, 0.2, 0.05, 0.05), 3) == 0.571
    assert r(expected_time_to_fill(2, 0.2, 0.05), 2) == 12.33
    # 4: slot values
    front, back = 0.7 * (2.5 - 0.4), 0.06 * (2.5 - 0.9)
    assert (r(front), r(back, 3), r(front - back), r(5 * (front - back), 2)) == (1.47, 0.096, 1.37, 6.87)
