"""Numbers gate: every numerical answer printed in Book 16, chapter 4 (text and solutions)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_fund as m  # noqa: E402

ft = m.ft


def r(x, d=2):
    return round(float(x), d)


def test_free_ride():
    d, _ = m.free_ride()
    assert (r(d["pooled"][0]), r(d["pooled"][1]), r(d["series"][0]), r(d["series"][1])) == (1.0, 1.11, 1.0, 3.33)
    assert r(d["series"][1] - d["pooled"][1]) == 2.22


@pytest.mark.reference
def test_crystallisation():
    c = m.crystallisation()
    assert (r(100 * c[1]), r(100 * c[3]), r(100 * c[12])) == (11.54, 11.26, 10.78)


def test_crystallisation_small_and_two_months():
    c = m.crystallisation(seeds=range(1, 21))
    assert c[1] >= c[3] >= c[12] > 0
    assert r(ft.crystallised([0.10, -0.10], 0.2, 1), 3) == 0.02 and ft.crystallised([0.10, -0.10], 0.2, 2) == 0.0


def test_public_record():
    pf = {int(x["days"]): x for x in m.form_pf()}
    assert (pf[7]["investor_pct"], pf[7]["portfolio_pct"], pf[30]["investor_pct"], pf[30]["portfolio_pct"]) == (
        9.0, 51.8, 19.1, 61.1)
    ratios = {d: pf[d]["portfolio_pct"] / pf[d]["investor_pct"] for d in pf}
    assert min(ratios, key=ratios.get) == 365
    rs = m.restrictions()
    assert [r(100 * rs[k] / rs["nav"], 1) for k in ("gated", "side_pocketed", "suspended")] == [2.5, 2.2, 0.5]
    assert r(100 / 8, 1) == 12.5


def test_stress_table():
    t = m.stress_table()
    want = {("hedge funds", "liquid first"): (30, 0.04, 31.1), ("hedge funds", "pro rata"): (30, 5.39, 51.8),
            ("hedge funds", "gate 10%"): (10, 0.01, 46.4), ("hedge funds", "liquid first, swing"): (30, 0.0, 31.1),
            ("illiquid fund", "liquid first"): (30, 1.69, 0.0), ("illiquid fund", "pro rata"): (30, 8.81, 8.0),
            ("illiquid fund", "gate 10%"): (10, 0.09, 0.0), ("illiquid fund", "liquid first, swing"): (30, 0.0, 0.0)}
    for k, (paid, dil, liq) in want.items():
        p, _, d, lq = t[k]
        assert (r(100 * p, 0), r(100 * d), r(100 * lq, 1)) == (paid, dil, liq)
    assert r(100 * ft.max_redemption(m.hedge_fund_ladder(), 7, 0.01), 1) == 51.8
    assert r(100 * ft.max_redemption(m.illiquid_ladder(), 7, 0.01), 1) == 8.0


def test_exercises():
    lad = [ft.Bucket(7, 0.20, 0.005), ft.Bucket(90, 0.80, 0.04)]
    a = ft.redeem(lad, 0.15, 7)
    assert r(100 * ft.ladder_share_within(a["ladder_after"], 7), 1) == 5.9
    first = ft.redeem(m.illiquid_ladder(), 0.05, 7, fire=m.FIRE)
    second = ft.redeem(first["ladder_after"], 0.05, 7, fire=m.FIRE)
    assert r(100 * ft.ladder_share_within(first["ladder_after"], 7), 2) == 3.16
    assert r(100 * ft.ladder_share_within(second["ladder_after"], 7), 2) == 0.0
