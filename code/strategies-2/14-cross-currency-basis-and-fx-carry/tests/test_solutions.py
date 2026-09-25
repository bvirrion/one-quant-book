"""Numbers gate: every numerical answer printed in Book 9, chapter 14 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_fxcarry import basis_results, carry_results, real  # noqa: E402


def pct(x, d=1):
    return round(100 * float(x), d)


def r(x, d=2):
    return round(float(x), d)


def test_carry():
    c = carry_results()
    assert (pct(c["raw"]["ann"], 2), r(c["raw"]["sr"]), r(c["raw"]["skew"]), pct(c["raw"]["worst"])) == (1.3, 0.23, -0.39, -6.6)
    assert (pct(c["hedged"]["ann"], 2), r(c["hedged"]["sr"]), r(c["hedged"]["skew"]), pct(c["hedged"]["worst"])) == (
        0.78, 0.15, 0.01, -4.3)
    assert (pct(c["cost"], 2), pct(c["payoff"], 2), c["periods"]) == (1.14, 0.63, 356)
    assert [pct(x) for x in c["crashes"]] == [-14.1, -15.5, -14.1]
    assert [(pct(a), pct(b)) for a, b in c["crash_months"]] == [(-12.0, -7.9), (-14.7, -14.3), (-14.4, -8.5)]
    assert r((1.3 - 0.78) / 1.3) == 0.4


def test_basis():
    b = basis_results()
    assert (r(b["mean_basis"], 1), r(b["qe_basis"], 1), r(b["ye_basis"], 1), r(b["always_bp"], 1), r(b["qe_bp"], 1),
            b["qe_days_a_year"], r(b["qe_rate"], 1)) == (-26.2, -49.8, -80.4, 11.2, 6.7, 40.0, 42.5)


def test_real():
    x = real()
    assert (x["first"], x["last"], x["months"], pct(float(x["ann_return"])), pct(float(x["ann_vol"])), r(float(x["sharpe"])),
            r(float(x["skew"])), pct(float(x["worst"])), x["worst_at"], pct(float(x["autumn_2008"])),
            pct(float(x["carry_part"])), pct(float(x["spot_part"]))) == (
        "2002-05", "2025-12", "284", 2.7, 7.2, 0.37, -0.6, -10.5, "2008-10", -19.4, 3.1, -0.4)
    assert (x["long_NZD"], x["long_AUD"], x["long_NOK"], x["short_CHF"], x["short_JPY"], x["short_SEK"], x["short_EUR"]) == (
        "271", "218", "188", "284", "177", "166", "159")


def test_exercises():
    c = carry_results(vol_mult=1.0)
    assert (pct(c["cost"], 2), pct(c["payoff"], 2), r(c["hedged"]["sr"]), r(c["hedged"]["skew"])) == (0.55, 0.63, 0.26, 0.02)
    x = real()
    assert r(float(x["ann_return"]) / float(x["ann_vol"])) == 0.37 and round(2.7 / 7.2, 3) == 0.375
    assert (r((50 - 15) / 252 * 10), r((1.14 - 0.63) / 1.3), r(20 / 7.2), r(-19.4 * 20 / 7.2, 0)) == (1.39, 0.39, 2.78, -54.0)
    assert round(2.7 * 20 / 7.2, 1) == 7.5
