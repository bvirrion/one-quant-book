"""Numbers gate: every numerical answer printed in Book 11, chapter 1 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import hf_business as b  # noqa: E402

econ = b.econ


def r(x, d=2):
    return round(float(x), d)


def test_public_record():
    p = b.public()
    assert r(p["virtu_anti_day"]) == 8.63 and r(p["virtu_mm_day"]) == 6.71 and r(100 * p["virtu_mm_share"], 1) == 77.7
    assert r(p["virtu_fixed"], 1) == 939.6 and r(p["virtu_fixed_day"]) == 3.78 and r(p["virtu_comm_data_day"], 1) == 1.0
    assert r(p["virtu_comp_per_employee"]) == 0.51 and r(p["virtu_anti_per_employee"]) == 2.09
    assert r(p["flow_capture_bp"]) == 2.50 and r(p["flow_fixed_per_fte"]) == 0.32
    assert r(100 * p["flow_ebitda_margin"], 0) == 41 and r(p["flow_tech_share_fixed"], 2) == 0.35


def test_small_firm():
    s = b.small_firm()
    assert r(s["breakeven"] / 1e9) == 1.33 and s["profit"] == 20_000 and r(s["leverage"], 1) == 3.0
    assert r(econ.profit(1.8e9, 0.5e-4, 0.2e-4, 40_000.0), 0) == 14_000
    assert 250 * s["profit"] == 5.0e6
    assert r(econ.breakeven_volume(0.5e-4, 0.2e-4, 50_000.0) / 1e9) == 1.67
    assert r(econ.breakeven_volume(0.4e-4, 0.2e-4, 40_000.0) / 1e9, 1) == 2.0
    assert r(econ.profit(2e9, 0.4e-4, 0.2e-4, 40_000.0), 6) == 0.0


def test_first_quoter():
    d, t = b.decomposition(10.0, "mid"), b.decomposition(10.0, "truth")
    assert [r(d[k]) for k in ("spread", "adverse", "inventory", "fees", "total")] == [186.5, -177.25, -66.5, 38.27, -18.98]
    assert [r(d["per_share"][k], 3) for k in ("spread", "adverse", "inventory", "fees", "total")] == [
        0.487, -0.463, -0.174, 0.1, -0.05]
    assert [r(t["per_share"][k], 3) for k in ("spread", "adverse", "inventory", "total")] == [-0.173, 0.038, -0.013,
                                                                                               -0.049]
    assert r(d["volume"], 0) == 38270 and r(100 * d["market_share"], 0) == 11 and r(d["messages"], 0) == 1256
    assert r(d["sd_total"], 0) == 89 and r(d["se_total"], 0) == 28


def test_curve_and_feedback():
    c = b.markout_curve("mid")
    i10, i20 = b.HORIZONS.index(10), b.HORIZONS.index(20)
    assert (r(c[0], 3), r(c[i10], 3), r(c[i20], 3)) == (0.487, 0.024, -0.06)
    assert b.feedback() == (336012, 323)


def test_exercise_7_and_iq6():
    mh = b.mh
    rows = [mh.run_tape(mh.SymmetricQuoter(100, 500), b.cfg(s), fees=mh.Fees(0, 0)) for s in b.SEEDS[:2]]
    base = [b.first_day(s) for s in b.SEEDS[:2]]
    assert all((x.fills == y.fills).all() for x, y in zip(rows, base, strict=True))
    d = b.decomposition(10.0, "mid")["per_share"]
    assert r(d["total"] - d["fees"], 3) == -0.150
    assert round((2 * 89 / 19) ** 2) == 88 and math.isclose(2145.3 / 248.5, 8.633, rel_tol=1e-3)
