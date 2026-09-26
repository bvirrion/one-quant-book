"""Numbers gate: every numerical answer printed in Book 11, chapter 13 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_basket as h  # noqa: E402

fb = h.fb


def r(x, d=2):
    return round(float(x), d)


def test_sweep():
    s = h.sweep(20.0)
    rows = [(r(s[k]["capture"]), r(s[k]["costs"]), r(s[k]["te"]), r(s[k]["mean"]), r(s[k]["sharpe"])) for k in (1, 5, 10, 15, 30, 50)]
    assert rows == [(1.44, 0.93, 1.74, 0.51, 0.29), (2.13, 1.21, 0.92, 0.92, 0.91), (2.17, 1.29, 0.62, 0.88, 1.24),
                    (2.10, 1.39, 0.44, 0.71, 1.33), (1.84, 1.52, 0.16, 0.32, 1.06), (1.72, 1.65, 0.0, 0.07, 0.32)]
    f = h.sweep(2.0)
    assert [r(f[k]["mean"]) for k in (1, 5, 10, 15, 30, 50)] == [0.57, 1.23, 1.36, 1.34, 1.28, 1.15]
    assert h.best(20.0) == {"mean": 5, "sharpe": 15} and h.best(2.0) == {"mean": 10, "sharpe": 50}
    assert h.best(20.0, 150.0) == {"mean": 2, "sharpe": 3} and h.best(20.0, 1000.0) == {"mean": 10, "sharpe": 40}
    assert round(100 * (f[10]["mean"] / s[5]["mean"] - 1)) == 48
    assert (r(s[5]["weight_held"]), r(s[5]["beta_held"]), r(s[15]["weight_held"], 1), r(s[15]["beta_held"])) == (0.73, 0.83, 0.9, 0.94)


def test_index_and_exercises():
    c = h.concentration()
    assert r(c["top10"], 1) == 0.5 and (r(c["hs_min"], 1), r(c["hs_max"], 1)) == (0.5, 1.7)
    assert r(fb.fair_future(5000, 0.05, 0.015, 0.25)) == 5043.94
    lo, hi = fb.basis_band(5000, 0.05, 0.015, 0.25, 1.0)
    assert (r(lo), r(hi)) == (5043.44, 5044.45)
    assert r(fb.hedge_ratio(1000, 5, 150)) == 1.33 and fb.hedge_ratio(50, 5) == 10
    assert r(h.dividend_shift_bp(), 1) == 5.0
    assert (r(math.exp(-200 / 400)), r(math.exp(-600 / 400))) == (0.61, 0.22)
    full = fb.trade(h.index(), 50, leg_us=0.0, lag_us=1e9, n_trades=100)
    assert r(full["capture"] - full["costs"]) == 1.35
