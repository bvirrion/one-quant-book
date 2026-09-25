"""Numbers gate: every numerical answer printed in Book 9, chapter 4 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_eventvol import by_error, crush, extraction, hedging, real  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def pct(x, d=1):
    return round(100 * float(x), d)


def test_event_hedging():
    h = hedging()
    got = {k: (pct(v["mean"]), pct(v["sd"], 0), r(v["per_event"], 3), pct(v["hedge_cost"], 2), r(v["annual"]))
           for k, v in h.items()}
    assert got == {"never": (2.0, 31, 0.064, 0.0, 0.91), "daily": (2.1, 29, 0.073, 0.06, 1.04),
                   "twice a day": (2.0, 28, 0.071, 0.18, 1.0), "every two hours": (1.8, 27, 0.064, 0.23, 0.91),
                   "hourly": (1.7, 27, 0.063, 0.3, 0.89), "band 0.05": (1.7, 27, 0.063, 0.24, 0.89),
                   "band 0.10": (2.0, 28, 0.07, 0.18, 1.0), "band 0.20": (1.9, 28, 0.068, 0.13, 0.96)}


def test_scalping_without_event():
    h = hedging(False)
    got = {k: (pct(v["mean"]), pct(v["sd"]), pct(v["hedge_cost"])) for k, v in h.items()}
    assert got == {"never": (-12.1, 62.4, 0.0), "daily": (-12.4, 15.3, 0.7), "twice a day": (-13.0, 11.5, 1.0),
                   "every two hours": (-13.4, 8.5, 1.5), "hourly": (-14.1, 6.7, 2.1), "band 0.05": (-13.7, 7.2, 1.6),
                   "band 0.10": (-13.0, 8.6, 1.2), "band 0.20": (-12.6, 12.6, 0.7)}


def test_bias_and_error():
    assert [pct(hedging(True, b)["daily"]["mean"]) for b in (0.0, -0.15, -0.30)] == [-2.2, -0.1, 2.1]
    e = by_error()
    assert [pct(x) for x in e["mean"]] == [8.0, 2.7, 3.9, 0.5, -4.5]
    assert [r(x) for x in e["err"]] == [-0.46, -0.3, -0.21, -0.11, 0.05]
    assert (r(e["corr"]), r(e["median_err"]), r(math.exp(e["median_err"]))) == (-0.13, -0.21, 0.81)


def test_crush_and_extraction():
    c = crush()
    assert (pct(c["iv_before"]), pct(c["iv_after"]), pct(c["fall"]), pct(c["gap_abs"], 2), pct(c["implied_abs"], 2)) == (
        36.6, 32.0, 8.6, 4.35, 3.62)
    x = extraction()
    assert (pct(x["v1"]), pct(x["v2"]), r(x["event_var"], 5), r(x["true_imp"], 5)) == (39.5, 32.3, 0.00135, 0.00135)
    assert pct(math.sqrt(0.00135), 2) == 3.67


def test_real():
    x = real()
    assert (x["statement_days"], x["first"], x["last"], pct(float(x["spx_abs_event"]), 2),
            pct(float(x["spx_abs_other"]), 2), r(float(x["spx_sq_event"]) / float(x["spx_sq_other"]), 3),
            pct(math.sqrt(float(x["spx_sq_event"]) - float(x["spx_sq_other"])), 2)) == (
        "125", "2011-01-26", "2026-09-16", 0.83, 0.71, 1.146, 0.41)
    assert (pct(float(x["vix9d_fell_event"])), pct(float(x["vix9d_fell_other"])), pct(float(x["vix9d_chg_event"]), 2),
            pct(float(x["vix9d_chg_other"]), 2), pct(float(x["vix_fell_event"])), pct(float(x["vix_fell_other"])),
            pct(float(x["vix_chg_event"]), 2), pct(float(x["vix_chg_other"]), 2)) == (
        65.6, 53.1, -3.05, 0.09, 56.0, 54.2, -1.1, 0.03)


def test_small_answers():
    h = hedging()
    assert pct(h["daily"]["mean"] - h["hourly"]["mean"]) == 0.4
    assert pct(math.sqrt(2 / math.pi) * 0.05, 2) == 3.99
    assert pct(math.sqrt(0.09 + 0.0025 / (10 / 252))) == 39.1
    assert r(math.sqrt(200), 1) == 14.1
