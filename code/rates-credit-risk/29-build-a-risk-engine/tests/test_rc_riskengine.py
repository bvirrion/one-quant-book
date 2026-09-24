"""Tests of the chapter 29 teaching module (Book 6)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import numpy as np
import rc_riskengine as m


def test_book_and_market():
    b = m.book()
    assert len(b) == 1000 and len({t.trade_id for t in b}) == 1000
    md = m.market()
    assert md.asof.isoformat() == "2026-09-23" and md.spots["EURUSD"] == 1.1411


def test_scenarios():
    for h in (1, 10):
        s = m.scenarios(h)
        assert len(s) == 250 and len(s[0].bumps) == 9


def test_euler_adds_up():
    r = m.reports(10)["full"]
    assert abs(sum(m.euler().values()) - r[("Firm",)]["es"]) < 1e-6


def test_plan_matches_full_on_rate_options():
    r = m.revaluations(10)
    idx = [j for j, t in enumerate(m.book()) if t.path[-1] == "Options"]
    assert np.allclose(r["plan"]["pnl"][:, idx], r["full"]["pnl"][:, idx])
