"""Numbers gate: every numerical answer printed in Book 17, chapter 25 (text and solutions)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_leader as a  # noqa: E402

fr = a.fr


def r(x, d=2):
    return round(float(x), d)


@pytest.mark.reference
def test_partner():
    s = a.summary(a.run())
    assert (r(s["income"]), r(s["income_p10"]), r(s["income_p90"])) == (8.93, 5.79, 12.14)
    assert (r(s["capital5"]), r(s["capital5_p05"]), r(100 * s["below"], 1)) == (6.67, 3.32, 9.4)
    assert (r(s["by_year_draw"][0]), r(s["by_year_draw"][2]), r(s["by_year_cap"][0])) == (1.81, 1.76, 2.15)
    pts, share = a.break_even()
    assert round(pts) == 20 and r(100 * share) == 0.66
    s8 = a.summary(a.run(payout=0.8))
    assert (r(s8["income"]), r(s8["capital5"]), r(100 * s8["below"], 1)) == (11.91, 3.69, 13.1)


def test_arithmetic_and_evidence():
    assert r(100 * 30 / 3030) == 0.99 and r(100 * 30 / 3120) == 0.96
    assert (r(300 * 30 / 3030), r(0.6 * 300 * 30 / 3030), r(0.4 * 300 * 30 / 3030)) == (2.97, 1.78, 1.19)
    assert {k: fr.smf_count(k) for k in fr.SMF_TIERS} == {"limited scope": 3, "core": 6, "enhanced": 17}
    e = a.eba_mb()
    mf = e[("credit institutions", "MB Management function")]
    assert (int(mf["high_earners"]), r(float(mf["avg_total_eur"]) / 1e6), r(float(mf["variable_to_fixed"]))) == (
        586, 2.10, 0.73)
    inv = e[("investment firms", "MB Management function")]
    assert (int(inv["high_earners"]), r(float(inv["avg_total_eur"]) / 1e6), r(float(inv["variable_to_fixed"]))) == (
        61, 1.99, 2.07)
    s = a.survey()
    ce = s["11-1011"]
    assert [int(ce[k]) for k in ("employment", "p10", "p50", "p90")] == [4700, 186_460, 431_020, 749_840]
    assert (int(s["11-3021"]["p50"]), int(s["11-1021"]["p50"]), int(s["11-3031"]["p50"])) == (214_460, 198_900, 223_860)
    assert 5 * a.ALTERNATIVE == 6.0


def test_small_runs():
    d = a.run(n=200)
    assert d["draws"].shape == (200, 5) and (d["draws"] >= 0).all()
    import numpy as np
    one = fr.partner_path(100.0, 0.0, 1, 50, 50, 0.0, 0.5, 99, 0, 1, 1, np.random.default_rng(0))
    assert one["draws"][0, 0] == pytest.approx(0.5 * 100 * 0.5)
    assert fr.card("partner").chapter == 25
