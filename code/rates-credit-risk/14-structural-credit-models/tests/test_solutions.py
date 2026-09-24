"""Numbers gate: every numerical answer printed in Book 6, chapter 14 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_structural as m
from firm_structural import (
    asset_from_equity,
    distance_to_default,
    equity_vol,
    invert,
    merton_debt,
    merton_equity,
    merton_pd,
    merton_spread,
    ncdf,
)

F = m.firm()
H = m.hedge()
M = m.may_2005()


def test_text():
    assert (round(F["V"], 2), round(100 * F["sigma"], 1), round(F["debt"], 2)) == (40.69, 15.6, 30.69)
    assert round(1e4 * F["spread"]) == 130 and round(100 * F["pd_rn"], 1) == 32.7
    assert round(F["dd"], 2) == 1.02 and round(100 * F["pd_real"], 1) == 15.4
    assert 3 < 0.5 / F["sigma"] < 3.5
    ts = [round(1e4 * m.fp_spread(F["V"], F["sigma"], t)) for t in (1, 2, 3, 5, 10)]
    assert ts == [64, 173, 216, 229, 197]
    assert round(100 * m.fp_survival(F["V"], F["sigma"], 5), 1) == 82.3
    assert round(100 * m.implied_barrier(), 1) == 78.7
    assert round(H["ds_dE"], 4) == -0.0047 and round(H["cs01"]) == -3_713
    assert round(H["dv_dE"]) == 174_423 and round(H["short_equity"] / 1e6, 2) == 1.74
    assert (round(1e4 * M["model0"], 1), round(1e4 * M["model1"], 1)) == (228.7, 160.7)
    V1 = asset_from_equity(m.E0 * 1.18, F["sigma"], m.D, m.T, m.R_FREE)
    assert round(100 * equity_vol(V1, m.D, m.T, m.R_FREE, F["sigma"]), 1) == 47.1
    V2, s2 = invert(m.E0 * 1.18, 0.5, m.D, m.T, m.R_FREE)
    assert round(100 * s2, 1) == 17.3 and round(1e4 * m.fp_spread(V2, s2)) == 251


def test_exercises():
    e, d = merton_equity(50, 40, 5, 0.04, 0.2), merton_debt(50, 40, 5, 0.04, 0.2)
    assert (round(e, 2), round(d, 2), round(1e4 * merton_spread(50, 40, 5, 0.04, 0.2))) == (18.89, 31.11, 103)
    assert round(100 * merton_pd(50, 40, 5, 0.04, 0.2), 1) == 23.5
    assert round(distance_to_default(F["V"], 40, 1, 0.08, F["sigma"]), 2) == 0.54
    assert round(100 * merton_pd(F["V"], 40, 1, 0.08, F["sigma"]), 1) == 29.3
    assert round(100 * (2 * ncdf(math.log(1.5) / (0.3 * math.sqrt(2))) - 1), 1) == 66.1
    assert round(2 * H["short_equity"] / 1e6, 2) == 3.49
    assert round(0.5 / F["sigma"], 1) == 3.2
    assert round(1e4 * m.fp_spread(F["V"], F["sigma"], 10, m.implied_barrier())) == 380


def test_problem():
    assert round(1e4 * (m.MARKET_SPREAD - M["model0"])) == 271
    assert round(1e4 * M["predicted"]) == 432 and round(1e4 * M["model1"]) == 161
    assert round(M["equity_pnl"]) == -313_961 and round(M["cds_pnl_model"]) == 259_002
    assert round(M["hedged_model"]) == -54_958
    assert round(M["cds_pnl"]) == -689_903 and round(M["total"]) == -1_003_863
    h = 1e-3
    e1 = m.E0 * 1.18
    assert round((m.model_spread_at_equity(e1 + h) - m.model_spread_at_equity(e1 - h)) / (2 * h), 4) == -0.0030
    lo, hi = 0.0, 0.05
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        lo, hi = (lo, mid) if m.seller_value(mid) - m.seller_value(0.05) < -M["equity_pnl"] else (mid, hi)
    assert round(1e4 * mid) == 418 and round(1e4 * (0.05 - mid)) == 82
