"""Numbers gate: every numerical answer printed in Book 2, Chapter 11 (text and solutions)."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/breakeven"))
from firm_breakeven import breakeven, contingency_index, forward_index, index_ratio, ref_index, zc_swap_payment
from inflation_demo import DATED, TIPS, august_2022, hook_2022, load_cpi, load_tips10, seasonality

CPI = load_cpi()
H = hook_2022()
A = august_2022()
S = seasonality()
Y = {d: (n, r, b) for d, n, r, b in load_tips10()}


def test_hook_and_text():
    assert round(H["cpi_jun"] * 100, 1) == 9.1
    assert (round(H["index_only"] * 100, 1), round(H["price_only"] * 100, 1), round(H["total"] * 100, 1)) == (
        7.7, -21.3, -15.2)
    assert ref_index(dt.date(1996, 4, 15), {(1996, 1): 154.40, (1996, 2): 154.90}) == 154.63333
    assert (CPI[(2021, 10)], CPI[(2021, 11)], CPI[(2022, 5)], CPI[(2022, 6)], CPI[(2022, 7)]) == (
        276.589, 277.948, 292.296, 296.311, 296.276)
    assert A["ref_dated"] == 277.20274 and A["ref_aug15"] == 294.10922
    assert index_ratio(dt.date(2022, 8, 15), DATED, CPI) == 1.06099
    assert index_ratio(dt.date(2022, 7, 15), DATED, CPI) == 1.04814
    assert round(TIPS.coupon / 200 * 1e8 * 1.04814) == 65_509
    assert round(breakeven(0.0267, 0.0014) * 100, 4) == 2.5265
    assert Y["2022-07-29"] == (2.67, 0.14, 2.53) and Y["2022-12-30"][1:] == (1.58, 2.30)
    assert round(Y["2022-12-30"][1] - (-0.97), 2) == 2.55
    assert round(forward_index(300, 0.025, 5), 2) == 339.42
    assert round(zc_swap_payment(1e8, 300, 345, 0.025, 5) / 1e6, 2) == 1.86
    assert round(A["accrual"] * 100, 2) == 1.37 and round(A["accrual_annualised"] * 100, 1) == 17.8
    assert round(sum(S[m] for m in (10, 11, 12)), 2) == -0.85 and round(4 * sum(S[m] for m in (10, 11, 12)), 1) == -3.4
    assert max(S, key=S.get) == 3 and min(S, key=S.get) == 11
    assert CPI[(2024, 9)] == 315.301 and CPI[(2025, 9)] == 324.8
    assert round(contingency_index(324.800, 315.301), 3) == 325.604


def test_exercises():
    a, b = seasonality(2010, 2019), S
    assert (round(a[3], 3), round(a[11], 3)) == (0.355, -0.376)
    assert round(max(abs(a[m] - b[m]) for m in a), 2) == 0.11 and max(a, key=lambda m: abs(a[m] - b[m])) == 6
    assert [round(S[m], 3) for m in (10, 11, 12)] == [-0.144, -0.359, -0.349]


def test_problem():
    assert (A["ref_aug1"], A["ref_sep1"], A["ir"]) == (292.296, 296.311, 1.05445)
    assert round(A["accrual"] * 100, 3) == 1.374 and round(A["price"], 3) == 99.865
    assert round(A["mv"] / 1e6, 2) == 105.30
    assert round(A["accrual_income"]) == 1_446_444 and round(A["real_pull"]) == 12_513
    assert round(A["carry"] - A["accrual_income"] - A["real_pull"] + A["repo_cost"]) == 172
    assert round(A["repo_cost"]) == 208_558 and round(A["carry"]) == 1_250_572
    assert round(A["nominal_carry"]) == 27_366
    assert round(A["sep_accrual"] * 100, 3) == -0.012 and round(A["sep_carry"]) == -202_160
    assert round(A["dv01"]) == 98_921 and round(A["carry"] / A["dv01"], 1) == 12.6
    assert round(A["ir"], 3) == 1.054 and round((1 / A["ir"] - 1) * 100) == -5
    assert round(A["carry"] / 1e6, 2) == 1.25
