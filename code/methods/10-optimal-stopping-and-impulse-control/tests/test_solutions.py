"""Numbers gate: every numerical answer printed in Book 4, Chapter 10 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_bands import GAMMA, SIGMA, K, band_cost, dp_stopping_check, optimal_fixed_band, problem, simulate_band

P = problem()
D = dp_stopping_check()


def test_text():
    assert (round(P["b_fix"], 1), round(P["cost_fix"]), round(1 / P["trades_per_day"])) == (34.6, 200, 3)
    assert round(P["daily_cost"]) == 400 and round(100 * P["saving"]) == 50 and round(100 * P["narrowing"]) == 16
    assert (round(D["theta"], 4), round(D["b_star"], 1), round(D["b_grid"], 1)) == (0.0351, 33.5, 32.2)
    assert (round(D["v_at_0"], 2), round(D["v_theory_at_0"], 2)) == (8.79, 8.80)
    assert round(0.5826 * 2, 1) == 1.2
    assert round(band_cost(10.0, 0.0, SIGMA, GAMMA, K)) == 1208
    assert (round(P["b_prop"], 1), round(P["cost_prop"])) == (24.7, 304)
    assert (round(P["b_both"], 1), round(P["a_both"], 1), round(P["cost_both"])) == (42.4, 12.8, 418)
    assert (round(100 ** 0.25, 1), round(100 ** (1 / 3), 1)) == (3.2, 4.6)
    assert round(0.5 / 0.02) == 25 and 1 / D["theta"] >= 0.5 / 0.02


def test_exercises():
    assert (round(optimal_fixed_band(SIGMA, GAMMA, 2 * K)[0], 1), round(optimal_fixed_band(SIGMA, GAMMA, 2 * K)[1])) == (41.2, 283)
    assert (round(optimal_fixed_band(2 * SIGMA, GAMMA, K)[0], 1), round(optimal_fixed_band(2 * SIGMA, GAMMA, K)[1])) == (49.0, 400)
    assert round(1 / D["theta"], 1) == 28.5
    assert (round(P["sim_cost"], 1), round(P["sim4_cost"], 1)) == (197.5, 199.6)


def test_problem():
    assert (round(P["b_half"], 1), round(optimal_fixed_band(SIGMA, GAMMA, K / 2)[1])) == (29.1, 141)
    assert round(P["risk_share"], 2) == 0.5


def test_time_step_and_ablation():
    """WRITING section 9. The simulated band cost converges to the formula as the check interval is
    divided by four (197.5 -> 199.6 -> 200, an O(sqrt(dt)) overshoot effect), and each cost credited
    for the band's existence is ablated: with no fee the optimal band shrinks to zero; with no risk
    charge it grows without bound."""
    gap1, gap4 = abs(P["sim_cost"] - 200), abs(P["sim4_cost"] - 200)
    assert gap4 < gap1 and gap4 < 1.0
    assert optimal_fixed_band(SIGMA, GAMMA, 1e-9)[0] < 0.5
    assert optimal_fixed_band(SIGMA, 1e-9, K)[0] > 1000
    sim = simulate_band(P["b_fix"], 0.0, SIGMA, GAMMA, K, 0.0, T=5000.0, dt=1 / 390, seed=9)
    assert abs(sim["avg_cost"] - 200) < 10 and math.isfinite(sim["avg_cost"])
