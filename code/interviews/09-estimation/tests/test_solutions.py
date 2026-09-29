"""Numbers gate: every numerical answer printed in Book 18, chapter 9 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_fermi import (
    CME_ADV_CONTRACTS_2025,
    FX_TURNOVER_USD_PER_DAY,
    OPRA_CAPACITY_GBITS_PER_100MS,
    OPRA_PEAK_MSGS_1S,
    OPRA_PEAK_MSGS_10MS,
    WORLD_POPULATION_2024,
    calibration_p_value,
    chain,
    combine_log_estimates,
    geometric_mean,
    hit_rate,
    interval_factor,
    interval_score,
    product_log_sd,
)


def inside(x, lo, hi):
    return lo <= x <= hi


def test_hook_and_example_opra():
    assert chain(5_000, 17, 10) == 850_000
    assert inside(OPRA_PEAK_MSGS_10MS, 200_000, 2_000_000)
    assert round(math.sqrt(200_000 * 2_000_000)) == 632_456


def test_text_log_errors():
    assert round(product_log_sd([0.35] * 4), 2) == 0.70
    assert round(interval_factor(0.7), 2) == 3.16
    assert round(interval_factor(0.35), 2) == 1.78
    # a product of four factors each within a factor 2 at 90%: each log sd ln2 / 1.645
    s = math.log(2) / 1.645
    assert round(s, 2) == 0.42 and round(interval_factor(product_log_sd([s] * 4)), 1) == 4.0


def test_figure_numbers():
    assert round(100 * hit_rate(0.9, 0.5, 1), 1) == 58.9
    assert round(100 * hit_rate(0.5, 0.5, 1), 1) == 26.4
    assert round(100 * hit_rate(0.9, 1, 1), 6) == 90


def test_q1_coffee():
    assert chain(400, 2, 220, 0.25) == 44_000


def test_q2_seconds():
    assert 365 * 24 * 3600 == 31_536_000
    assert 252 * 6.5 * 3600 == 5_896_800


def test_q3_geometric_mean():
    assert geometric_mean(200, 20_000) == 2_000


def test_q4_fx():
    assert inside(FX_TURNOVER_USD_PER_DAY, 3e12, 15e12)
    assert round(math.sqrt(3e12 * 15e12) / 1e12, 1) == 6.7


def test_q5_opra():
    assert inside(OPRA_PEAK_MSGS_10MS, 200_000, 2_000_000)


def test_q6_cme():
    # chain: 50 active products x 500 thousand contracts a day each, with a long tail
    assert chain(50, 500_000) == 25_000_000
    assert inside(CME_ADV_CONTRACTS_2025, 10e6, 60e6)
    assert round(CME_ADV_CONTRACTS_2025 / 1e6, 1) == 28.1


def test_q7_birthdays():
    assert round(WORLD_POPULATION_2024 / 365.25 / 1e6, 1) == 22.5


def test_q8_bytes():
    assert chain(5_000, 20_000, 32) == 3.2e9


def test_q9_calibration():
    assert round(calibration_p_value(5, 10, 0.9), 4) == 0.0016
    assert round(10 * 0.9, 1) == 9.0


def test_q10_product_interval():
    assert round(interval_factor(product_log_sd([0.35] * 4)), 2) == 3.16


def test_q11_combine():
    est, sd = combine_log_estimates([1e6, 1e7], [0.7, 1.0])
    assert round(est / 1e6, 1) == 2.1 and round(sd, 2) == 0.57


def test_q12_interval_score():
    assert interval_score(5e12, 12e12, FX_TURNOVER_USD_PER_DAY, 0.1) == 7e12
    assert round(interval_score(2e12, 5e12, FX_TURNOVER_USD_PER_DAY, 0.1) / 1e12, 1) == 95.0


def test_q13_bandwidth():
    gbps = OPRA_PEAK_MSGS_1S * 40 * 8 / 1e9
    assert round(gbps, 1) == 20.4
    assert round(OPRA_CAPACITY_GBITS_PER_100MS * 10, 1) == 44.0


def test_q4_chain_and_q11_consistency():
    assert 30e12 * 50 / 250 == 6e12 and 30e12 * 100 / 250 == 12e12
    d = math.log(1e7) - math.log(1e6)
    sd = math.sqrt(0.7**2 + 1.0**2)
    assert round(sd, 2) == 1.22 and round(d / sd, 1) == 1.9
    assert round(1 / 0.7**2, 2) == 2.04 and round(1 / math.sqrt(1 / 0.49 + 1), 2) == 0.57
    assert OPRA_PEAK_MSGS_10MS * 100 == 89e6


def test_worked_answers():
    lg = math.log10(3.7) + math.log10(2.2) + math.log10(0.45)
    assert round(math.log10(3.7), 2) == 0.57 and round(math.log10(2.2), 2) == 0.34 and round(math.log10(0.45), 2) == -0.35
    assert round(lg + 7, 2) == 7.56 and round(10**0.56, 1) == 3.6
    assert round(3.7e3 * 2.2e4 * 0.45 / 1e7, 3) == 3.663
    first = 2000 * 5 * 23_400
    assert round(first / 1e8, 1) == 2.3
    sd1 = math.log(3) / 1.645
    sd = sd1 * math.sqrt(2)
    fac = math.exp(1.645 * sd)
    assert round(sd1, 2) == 0.67 and round(sd, 2) == 0.94 and round(fac, 1) == 4.7
    assert round(first / fac / 1e7) == 5 and round(first * fac / 1e9, 1) == 1.1
    per_s = 10**7 / (8 * 50)
    assert per_s == 25_000 and round(per_s * 23_400 / 1e8, 2) == 5.85
    assert round(per_s * 23_400 / first, 1) == 2.5
