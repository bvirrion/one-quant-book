import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_alm as f


def test_supervisory_shock_shapes():
    assert f.shock_curve("parallel_up")(7.0) == 0.02
    assert math.isclose(f.shock_curve("short_up")(0.0), 0.03)
    s = f.shock_curve("steepener")
    assert s(0.25) < 0 < s(20.0)
    fl = f.shock_curve("flattener")
    assert fl(0.25) > 0 > fl(20.0)


def test_bond_duration_and_price_change():
    assert math.isclose(f.bond_price_change(0.03, 5, 0.03, 0.03), 0.0, abs_tol=1e-15)
    d = f.duration(0.03, 10, 0.03)
    assert abs(f.bond_price_change(0.03, 10, 0.03, 0.0301) + d / 1.03 * 1e-4) < 1e-6


def test_eve_of_a_matched_book_is_immune():
    a = f.Position("a", "asset", 100.0, 0.02, 5.0)
    lia = f.Position("l", "liability", 100.0, 0.02, 5.0)
    dep = f.Deposits(0.0, 0.5, 5.0, 0.0, 0.3, 0.1)
    b = f.BalanceSheet([a, lia], dep, 0.02)
    assert all(abs(v) < 1e-9 for v in b.delta_eve().values())


def test_lcr_caps_and_ftp():
    p1 = f.Position("c", "asset", 10.0, 0.0, 0.0, "cash", hqla="L1")
    p2 = f.Position("m", "asset", 100.0, 0.02, 5.0, hqla="L2A")
    r = f.lcr([p1, p2], [(100.0, 0.10)], 0.02)
    assert math.isclose(r["level2"], 2 / 3 * 10.0) and math.isclose(r["lcr"], (10 + 20 / 3) / 10.0)
    assert f.ftp_rate(lambda t: 0.04, lambda t: 0.001 * t, 5.0) == 0.045
    assert f.run_capacity(30.0, 150.0) == 0.2
