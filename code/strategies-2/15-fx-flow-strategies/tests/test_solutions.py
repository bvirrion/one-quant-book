"""Numbers gate: every numerical answer printed in Book 9, chapter 15 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_fxflows import real, results  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_synthetic():
    x = results()
    assert (r(x["push_sd"], 1), r(x["est_corr"]), r(x["trade"]["mean"], 1), r(x["trade"]["t"], 1), r(x["trade"]["sr"])) == (
        12.2, 0.94, 12.2, 5.4, 0.99)
    assert [(r(g["est_bp"], 1), r(g["mean"], 1)) for g in x["quintiles"]] == [(1.3, 0.2), (4.5, 12.0), (7.7, 17.7),
                                                                              (12.8, 9.5), (23.4, 21.8)]
    assert (r(x["fade_after"]["mean"], 1), r(x["fade_after"]["t"], 1)) == (10.2, 4.9)
    assert (r(x["fix"]["mean"]), r(x["fix"]["t"], 1), r(x["fix"]["sr"])) == (0.75, 2.7, 0.5)


def test_real():
    x = real()
    assert (x["first"], x["last"]) == ("1999-01-04", "2026-09-18")
    got = {k: (x[f"k{k}_months"], r(float(x[f"k{k}_corr"])), r(float(x[f"k{k}_t"]), 1), r(float(x[f"k{k}_trade_bp"]), 1),
               r(float(x[f"k{k}_trade_t"]), 1)) for k in (2, 3, 5)}
    assert got == {2: ("332", -0.18, -3.3, 11.4, 3.4), 3: ("332", -0.07, -1.4, 7.4, 1.9), 5: ("332", -0.03, -0.6, 13.7, 2.8)}
    assert r(float(x["k2_slope"]), 4) == -0.0248


def test_exercises():
    import math

    import numpy as np
    from firm_fxflows import FlowFXConfig, flow_trade, simulate_months
    cfg = FlowFXConfig(est_error=1.0)
    s = simulate_months(cfg)
    p = flow_trade(s, cfg)
    assert (r(np.corrcoef(s["est"], s["flow"])[0, 1]), r(p.mean(), 1), r(p.mean() / p.std(ddof=1) * math.sqrt(12))) == (
        0.56, 10.9, 0.87)
    assert (0.5 * 105 - 0.5 * 100, r(3.4 / math.sqrt(332) * math.sqrt(12)), 1114918000 / 5) == (2.5, 0.65, 222983600.0)
