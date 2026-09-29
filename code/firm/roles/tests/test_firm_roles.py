"""Acceptance tests for firm.roles."""
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_roles as fr  # noqa: E402


def test_registry():
    c = fr.card("trader")
    assert c.chapter == 16 and "market maker" in c.firm_types
    with pytest.raises(ValueError):
        fr.register(c)


def test_lca_cells():
    rows = [dict(fy="2025", kind="bank", role="trader", level="all", n="58", employers="5", suppressed="0",
                 p10="1", p25="2", p50="3", p75="4", p90="5"),
            dict(fy="2025", kind="systematic fund", role="trader", level="all", n="5", employers="3", suppressed="1",
                 p10="", p25="", p50="", p75="", p90="")]
    c = fr.lca_cells(rows, "trader")
    assert c["bank"]["p50"] == 3.0 and c["systematic fund"]["suppressed"] and "p50" not in c["systematic fund"]


def test_mm1_against_simulation():
    assert fr.mm1_wait_tail(2.0, 1.0, 0.1) == 1.0
    lam, mu, t = 0.5, 1.0, 1.0
    sim = fr.lindley_tail(lam, lambda n, rng: rng.exponential(1 / mu, n), t, 400_000, np.random.default_rng(3))
    assert abs(sim - fr.mm1_wait_tail(lam, mu, t)) < 0.01
    assert fr.mm1_wait_tail(lam, mu, t) == pytest.approx(0.5 * math.exp(-0.5))


def test_capacity_monotone():
    caps = [fr.max_strategies(a, 30, 60, 0.01) for a in (0.5, 1, 2, 4)]
    assert caps == sorted(caps, reverse=True) and caps[1] == 7
    assert fr.max_strategies(1, 30, 300, 0.01) > fr.max_strategies(1, 30, 60, 0.01)


def test_mmc_reduces_to_mm1():
    assert fr.mmc_wait_tail(1, 7.0, 120.0, 1 / 60) == pytest.approx(fr.mm1_wait_tail(7.0, 120.0, 1 / 60))
    assert fr.mmc_wait_tail(2, 14.0, 120.0, 1 / 60) < fr.mm1_wait_tail(7.0, 120.0, 1 / 60)


def test_feedback_speed():
    assert fr.years_to_significance(1.0, 252) == pytest.approx(3.8416 * (1 + 1 / 504), rel=1e-12)
    law = [fr.periods_to_significance(fr.fundamental_law_sr(0.02, 50, m), m) for m in (4, 12, 52, 252)]
    assert max(law) - min(law) < 1e-9


BOSS = {"validator": "head of validation", "head of validation": "chief risk officer", "chief risk officer": "ceo",
        "developer": "head of analytics", "head of analytics": "head of markets", "head of markets": "ceo",
        "owner": "head of markets", "risk dev": "head of risk analytics", "risk val": "head of risk analytics",
        "head of risk analytics": "chief risk officer", "desk val": "developer", "ceo": None}
SENIOR = {"chief risk officer", "head of markets"}


def test_bank_cards():
    assert {fr.card(n).chapter for n in ("desk strategist", "library quant", "risk quant", "model validator")} == {18}


def test_independence_grades():
    assert fr.independence(BOSS, SENIOR, "validator", "developer", "owner") == "a"
    assert fr.independence(BOSS, SENIOR, "validator", "risk dev") == "b"
    assert fr.independence(BOSS, SENIOR, "risk val", "risk dev") == "c"
    assert fr.independence(BOSS, SENIOR, "desk val", "developer") == "fail"
    assert fr.independence(BOSS, SENIOR, "desk val", "head of analytics") == "fail"
    with pytest.raises(ValueError):
        fr.chain({"x": "y", "y": "x"}, "x")


def test_validation_workload():
    one = dict(counts={1: 1}, full_hours={1: 100.0}, review_hours={1: 10.0}, interval_years={1: 1}, change_rate=0.0)
    assert fr.validation_hours(**one) == 100.0
    three = dict(one, interval_years={1: 4})
    assert fr.validation_hours(**three) == pytest.approx(25.0 + 7.5)
    assert fr.validator_headcount(**dict(one, change_rate=0.5), productive_hours=150.0) == pytest.approx(1.0)


def test_normalise_title():
    cases = {"Sr. Quant Developer - Equities": ("QUANTITATIVE DEVELOPER", "senior"),
             "VP, Quant Dev": ("QUANTITATIVE DEVELOPER", "vice president"),
             "Quantitative Developer II": ("QUANTITATIVE DEVELOPER", ""),
             "Lead SWE / C++": ("SOFTWARE ENGINEER", "lead"),
             "C++ Developer, Trading Systems": ("CPP DEVELOPER", ""),
             "Quant Dev L3": ("QUANTITATIVE DEVELOPER", "")}
    assert {t: fr.normalise_title(t) for t in cases} == cases
    assert fr.normalise_title(None) == ("", "")


def test_crosstab_and_gap():
    ct = fr.crosstab([("a", "x")] * 12 + [("a", "y")] * 3)
    assert ct[("a", "x")] == 12 and ct[("a", "y")] is None
    rng = np.random.default_rng(1)
    g = fr.median_gap(np.full(50, 150.0) + rng.normal(0, 1, 50), np.full(40, 100.0) + rng.normal(0, 1, 40), rng)
    assert g["diff_lo"] < g["diff"] < g["diff_hi"] and 49 < g["diff"] < 51 and 1.45 < g["ratio"] < 1.55
    assert fr.median_gap([1.0] * 9, [1.0] * 20, rng) is None
    assert fr.card("trading-system developer").chapter == 19


def test_percentile_ratio():
    r = fr.percentile_ratio({"p10": "100", "p50": 300.0, "p90": "#"}, {"p10": 50, "p50": 200, "p90": 400},
                            keys=("p10", "p50", "p90"))
    assert r == {"p10": 2.0, "p50": 1.5, "p90": None}
    assert fr.card("FPGA engineer").chapter == 20


def test_trend_two_points_and_poisson():
    tr = fr.filing_trend([2021, 2025], [100, 400])
    assert tr["rate"] == pytest.approx(math.log(4) / 4) and tr["se"] == pytest.approx(math.sqrt(1 / 100 + 1 / 400) / 4)
    assert tr["lo"] < tr["annual"] < tr["hi"]
    lo, hi = fr.poisson_interval(10)
    assert lo == pytest.approx(4.795, abs=1e-3) and hi == pytest.approx(18.39, abs=1e-2)
    assert fr.poisson_interval(0)[0] == 0.0
    three = fr.filing_trend([1, 2, 3], [100, 200, 400])
    assert three["rate"] == pytest.approx(math.log(2))
    assert fr.card("data engineer").chapter == 21


def test_pm_deal():
    rng = np.random.default_rng(0)
    d = fr.pm_deal(20.0, 2, 0.01, 100.0, 0.2, 0.0, 0.5, 0.9, 50, rng, days=20)
    assert not d["stopped"].any() and np.allclose(d["pay"], 0.2 * d["pnl"])
    d = fr.pm_deal(0.0, 1, 0.1, 100.0, 0.2, 10.0, 0.0, -1.0, 5, np.random.default_rng(1), days=10)
    assert d["stopped"].all() and np.allclose(d["pay"], 1.0) and (d["stop_day"] == 0).all()
    lo = fr.pm_deal(0.0, 3, 0.06, 1.0, 0.15, 0.0, 0.05, 0.075, 4000, np.random.default_rng(2), days=50)
    hi = fr.pm_deal(1.0, 3, 0.06, 1.0, 0.15, 0.0, 0.05, 0.075, 4000, np.random.default_rng(2), days=50)
    assert hi["stopped"].mean() < lo["stopped"].mean() and hi["pay"].mean() > lo["pay"].mean()
    assert fr.card("pod analyst").chapter == 22


def test_structuring_margin():
    sys.path.insert(0, str(pathlib.Path(fr.__file__).resolve().parents[1] / "autocall"))
    import firm_autocall as ac

    def make(c):
        return ac.TermSheet(obs_times=(1.0, 2.0), coupon=c, coupon_barrier=0.7, protection=0.6)

    m = fr.structuring_margin(make, 5.0, 2.0, 0.03, 0.02, 0.2, n=4000, seed=1, steps=4)
    v_fair, _ = fr.note_value(make(m["fair_coupon"]), 0.03, 0.02, 0.2, n=4000, seed=1, steps=4)
    assert v_fair == pytest.approx(98.0, abs=1e-9) and m["zero_margin_coupon"] > m["fair_coupon"]
    assert fr.card("structurer").chapter == 23


def test_pay_mix():
    assert fr.fixed_share(1.0) == 0.5 and fr.fixed_share(0.0) == 1.0
    g = fr.mix_gap(0.5, 1.0)
    assert g["ratio_of_ratios"] == 0.5 and g["fixed_control"] > g["fixed_business"]
    assert fr.card("compliance officer").chapter == 24


def test_leadership():
    assert (fr.smf_count("limited scope"), fr.smf_count("core"), fr.smf_count("enhanced")) == (3, 6, 17)
    d = fr.partner_path(100.0, 0.0, 1, 50, 50, 0.0, 0.5, 99, 0, 2, 3, np.random.default_rng(0))
    assert np.allclose(d["draws"], 25.0) and np.allclose(d["capital"][:, -1], 50.0)
    diluted = fr.partner_path(100.0, 0.0, 1, 50, 50, 0.0, 0.5, 2, 1, 2, 1, np.random.default_rng(0))
    assert diluted["draws"][0, 1] < diluted["draws"][0, 0]
    assert fr.card("head of desk").chapter == 25
