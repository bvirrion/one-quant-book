"""Numbers gate: every numerical answer printed in Book 5, Chapter 5 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_dividends import (
    CURVE,
    ForwardCurve,
    black,
    curve_from_chain,
    effective_vol,
    escrowed_call,
    htb_chain,
    htb_results,
    implied_borrow,
    model_smiles,
    spot_call,
)

H = htb_results()


def test_text():
    assert (round(H["put_mkt"], 2), round(H["call_mkt"], 2)) == (4.04, 2.78)
    assert (round(100 * H["iv_put_naive"]), round(100 * H["iv_call_naive"])) == (72, 47)
    assert (round(H["fwd"], 2), round(H["naive_fwd"], 2), round(100 * H["borrow"])) == (48.74, 50.16, 35)
    assert round(effective_vol(), 4) == 0.2552
    sm = {k: (a, b, c) for k, a, b, c in model_smiles([70, 130])}
    assert (round(100 * sm[70][1], 2), round(100 * sm[130][1], 2)) == (25.57, 25.49)
    assert round(100 * sm[70][0], 2) == 25.00
    assert round(spot_call(100) - escrowed_call(100), 1) == 0.2
    assert round(1 - 0.96 ** 5, 3) == 0.185                     # "almost a fifth"
    assert (round(H["df"], 5), round(100 * H["rate"], 2), round(H["carry"], 2)) == (0.99680, 3.90, 1.42)
    assert (round(H["call_naive"], 2), round(H["put_naive"], 2)) == (3.50, 3.34)
    assert round(-H["reversal_edge"], 2) == 1.42 and round(50 * 0.35 * 30 / 365, 2) == 1.44
    rows = curve_from_chain()
    assert max(abs(r["fwd"] - r["fwd_true"]) for r in rows) < 0.01
    assert 0.07 < max(abs(r["carry_step"] - r["carry_step_true"]) for r in rows) < 0.09


def test_exercises():
    assert round((100 - math.exp(-0.0075) - math.exp(-0.0225)) * math.exp(0.03), 4) == 101.0152
    assert round(95 + 7.02 / 0.985, 4) == 102.1269
    assert (round(4 * math.exp(-0.015), 4), round(100 / (100 - 4 * math.exp(-0.015)), 4)) == (3.9404, 1.0410)
    assert (round(math.exp(0.03), 4), round(0.96 * math.exp(0.03), 4)) == (1.0305, 0.9892)
    cv = ForwardCurve(100, 0.03, tuple((0.1 + 0.25 * i, 0.60) for i in range(12)), borrow=0.005)
    cv2 = ForwardCurve(100, 0.03, tuple((0.1 + 0.25 * i, 0.54) for i in range(12)), borrow=0.005)
    c1 = black(cv.forward(3), 100, 3, cv.df(3), 0.2, "C")
    c2 = black(cv2.forward(3), 100, 3, cv.df(3), 0.2, "C")
    assert (round(cv.forward(3), 4), round(cv2.forward(3), 4), round(c1, 4), round(c2, 4), round(c2 - c1, 4)) == (
        100.3611, 101.1038, 12.7558, 13.1475, 0.3917)
    r = curve_from_chain()[3]
    assert (round(r["fwd"], 4), round(r["df"], 5), round(CURVE.pv_cash(1.0), 4)) == (100.1132, 0.97033, 2.3661)
    assert round(100 * implied_borrow(100, r["fwd"], r["df"], 1.0, CURVE.pv_cash(1.0)), 3) == 0.504


def test_problem():
    diffs = [round(c - p, 2) for _, c, p in htb_chain()]
    assert diffs == [3.73, 1.23, -1.26, -3.75, -6.24]
    assert (round(H["call_err"], 2), round(H["put_err"], 2)) == (0.72, -0.70)
    assert round(100 * H["call_err"] / H["call_mkt"]) == 26
    assert (round(100 * H["iv_call_naive"], 1), round(100 * H["iv_put_naive"], 1)) == (47.3, 72.3)
    f5 = 50 * math.exp((0.04 - 0.05) * 30 / 365)
    df = math.exp(-0.04 * 30 / 365)
    assert round(f5, 2) == 49.96
    assert round(black(f5, 50, 30 / 365, df, 0.6, "C") - 2.78, 1) == 0.6
    assert round(4.04 - black(f5, 50, 30 / 365, df, 0.6, "P"), 1) == 0.6
