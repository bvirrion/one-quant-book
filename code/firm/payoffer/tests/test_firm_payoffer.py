"""Acceptance tests for firm.payoffer."""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_payoffer as po  # noqa: E402

R = 0.05
D = (1 + R) ** -np.arange(1, 10)


def rng(s=0):
    return np.random.default_rng(s)


def test_base_only_is_an_annuity():
    sim = po.simulate(po.Package("b", 100.0), 3, 0.0, R, 10, rng())
    assert np.allclose(sim["pv"], 100 * D[:3].sum())


def test_deferral_without_risk():
    p = po.Package("d", 100.0, median=60.0, deferral=0.5, vest_years=3)
    sim = po.simulate(p, 2, 0.0, R, 5, rng())
    upfront = 30 * (D[0] + D[1])
    deferred = 10 * (D[1] + D[2] + D[3]) + 10 * (D[2] + D[3] + D[4])
    assert np.allclose(sim["pv"], 100 * (D[0] + D[1]) + upfront + deferred)
    assert np.allclose(sim["forfeited"], 0.0)


def test_forfeiture_and_good_leaver():
    p = po.Package("d", 100.0, median=60.0, deferral=0.5, vest_years=3)
    s = po.simulate(p, 3, 0.0, R, 5, rng(), leave_year=1)
    assert np.allclose(s["forfeited"], 10 * (D[1] + D[2] + D[3]))
    g = po.Package("g", 100.0, median=60.0, deferral=0.5, vest_years=3, good_leaver=True)
    s2 = po.simulate(g, 3, 0.0, R, 5, rng(), leave_year=1)
    assert np.allclose(s2["forfeited"], 0.0) and np.allclose(s2["pv"] - s["pv"], s["forfeited"])


def test_sign_on_guarantee_and_buyout():
    p = po.Package("s", 100.0, median=10.0, sign_on=50.0, sign_on_years=1, guarantee=40.0)
    stay = po.simulate(p, 2, 0.0, R, 4, rng())
    go = po.simulate(p, 2, 0.0, R, 4, rng(), leave_year=1)
    assert np.allclose(stay["pv"], 50 + 100 * (D[0] + D[1]) + 40 * D[0] + 10 * D[1])
    assert np.allclose(go["pv"], 50 - 50 * D[0] + 100 * D[0] + 40 * D[0])
    b = po.Package("d", 100.0, median=60.0, deferral=0.5, vest_years=3)
    assert abs(po.buyout(b, 2, 10, rng()) - 10.0 * 5) < 1e-9


def test_certainty_equivalent():
    assert abs(po.certainty_equivalent(np.full(5, 7.0), 3.0, 100.0) - 7.0) < 1e-9
    x = np.array([0.0, 200.0])
    c1, c3 = po.certainty_equivalent(x, 1.0, 100.0), po.certainty_equivalent(x, 3.0, 100.0)
    assert c3 < c1 < 100.0 and abs(c1 - (np.sqrt(100 * 300) - 100)) < 1e-9
    with pytest.raises(ValueError):
        po.certainty_equivalent(np.array([-200.0]), 2.0, 100.0)


def test_formulaic_with_cut_and_noise():
    p = po.Package("f", 100.0, share=0.1, pnl_mean=1000.0, pnl_sd=1500.0, cut=-1000.0)
    s = po.simulate(p, 5, 0.0, R, 20000, rng(1))
    assert 0 < s["cut"].mean() < 1 and (s["leave"][s["cut"]] <= 5).all()
    sm = po.summary(s)
    assert sm["p10"] < sm["p50"] < sm["p90"]
    v = po.Package("v", 100.0, median=60.0, sigma=0.5, deferral=0.5, vest_years=3, inst_vol=0.3)
    m = po.summary(po.simulate(v, 3, 0.0, R, 40000, rng(2)))["mean"]
    exact = 100 * D[:3].sum() + 60 * np.exp(0.125) * (0.5 * D[:3].sum() + (0.5 / 3) * sum(
        D[t + k - 1] for t in range(1, 4) for k in range(1, 4)))
    assert abs(m / exact - 1) < 0.01
