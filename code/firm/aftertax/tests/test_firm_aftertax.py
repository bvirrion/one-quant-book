"""Acceptance tests for firm.aftertax against hand computations and the authorities' published figures."""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_aftertax as at  # noqa: E402

P = at.load(ROOT / "data/industry/tax_2026.csv", ROOT / "data/industry/ch_federal_tax_2026.csv")


def test_progressive():
    assert at.progressive(0, [(10, 0.1)]) == 0.0
    assert at.progressive(25, [(10, 0.1), (float("inf"), 0.2)]) == pytest.approx(4.0)


def test_uk_hand_case():
    r = at.net_local(P, "london", 100_000.0)
    assert r["tax"] == pytest.approx(0.2 * 37_700 + 0.4 * (87_430 - 37_700))
    assert r["social"] == pytest.approx(0.08 * 37_700 + 0.02 * 49_730)
    r2 = at.net_local(P, "london", 200_000.0)  # no personal allowance above 125,140
    assert r2["tax"] == pytest.approx(0.2 * 37_700 + 0.4 * (125_140 - 37_700) + 0.45 * (200_000 - 125_140))


def test_us_federal_and_payroll():
    assert at.progressive(1_000_000, P["us", "brackets"]) == pytest.approx(325_957.25)
    tax, social = at._us_federal(P, 300_000.0)
    assert social == pytest.approx(0.062 * 184_500 + 0.0145 * 300_000 + 0.009 * 100_000)


def test_new_york_recapture_continuous_and_flat():
    prev = at._new_york_state(P, 100_000.0)
    for g in range(100_500, 1_300_000, 500):
        t = at._new_york_state(P, float(g))
        assert t >= prev - 1e-6
        prev = t
    g = 800_000.0
    assert at._new_york_state(P, g) == pytest.approx(0.0685 * (g - 8_000))
    g = 2_000_000.0
    assert at._new_york_state(P, g) == pytest.approx(0.0965 * (g - 8_000))


def test_hong_kong_standard_rate_zone_matches_the_official_threshold():
    g = 2_132_500.0  # GovHK: single taxpayers approach the standard-rate zone here (2026/27)
    prog = at.progressive(g - P["hk", "basic_allowance"], P["hk", "brackets"])
    assert prog == pytest.approx(0.15 * g)


def test_singapore_and_swiss_table_points():
    assert at.progressive(1_000_000, P["sg", "brackets"]) == pytest.approx(199_150)
    assert at.progressive(320_000, P["sg", "brackets"]) == pytest.approx(44_550)
    assert at._ch_federal(P, 200_000.0) == pytest.approx(12_903.35)
    assert at._ch_federal(P, 100_050.0) == pytest.approx(2_684.35)  # income is rounded down to CHF 100
    assert at._ch_federal(P, 2_000_000.0) == pytest.approx(230_000.0)


def test_netherlands_credits_and_expat():
    lo = at.net_local(P, "amsterdam", 60_000.0)
    assert lo["tax"] < at.progressive(60_000, P["nl", "brackets"])  # credits apply at moderate income
    hi = at.net_local(P, "amsterdam", 300_000.0)
    assert hi["tax"] == pytest.approx(at.progressive(300_000, P["nl", "brackets"]))
    ex = at.net_local(P, "amsterdam", 300_000.0, expat=True)
    assert ex["tax"] == pytest.approx(at.progressive(300_000 - 78_600, P["nl", "brackets"]))


def test_dubai_and_conversion():
    assert at.net_usd(P, "dubai", 1e6)["net"] == 1e6
    k = at.local_per_usd(P, "london")
    assert k == pytest.approx(0.8567923137255 / 1.1299831372549)
    r = at.net_usd(P, "london", 1e6)
    assert 0 < r["avg_rate"] < at.marginal(P, "london", 1e6) < 0.5
