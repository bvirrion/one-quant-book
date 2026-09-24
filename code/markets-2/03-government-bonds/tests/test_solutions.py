"""Numbers gate: every numerical answer printed in Book 2, Chapter 3 (text and solutions)."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/bond"))
from bond_demo import FIVE, PAR, SETTLE, TEN, Y5, Y10, from_32nds, hedge, to_32nds
from firm_bond import Bond, bootstrap_par, thirty_360

D = dt.date
R10 = TEN.risk(Y10, SETTLE)
H = hedge()


def test_text():
    acc = TEN.accrued(SETTLE)
    assert round(acc * 1e4) == 4735 and round(acc * 1e5) == 47351
    assert from_32nds("100-12") == 100.375 and from_32nds("100-12+") == 100.390625
    assert round(TEN.dirty_price(Y10, SETTLE), 6) == 100.870911
    full = TEN.dirty_price(Y10 + 0.01, SETTLE) - R10["dirty"]
    lin = -R10["dirty"] * R10["modified"] * 0.01
    quad = lin + 0.5 * R10["dirty"] * R10["convexity"] * 1e-4
    assert (round(full, 3), round(lin, 3), round(quad, 3)) == (-7.675, -8.044, -7.662)
    # regulation examples quoted in the tutorial
    assert round(Bond(8.75, D(2020, 5, 15)).clean_price(0.0884, D(1990, 5, 15), treasury=True), 6) == 99.057893
    d = Bond(9.50, D(1995, 11, 15))
    assert round(d.clean_price(0.0954, D(1985, 11, 29), treasury=True), 6) == 99.730918
    # remark: the two conventions differ by a few thousandths of a point between coupons
    gap = abs(d.clean_price(0.0954, D(1985, 11, 29), treasury=True) - d.clean_price(0.0954, D(1985, 11, 29)))
    gap10 = abs(TEN.clean_price(Y10, SETTLE, treasury=True) - TEN.clean_price(Y10, SETTLE))
    assert 0.001 < gap < 0.01 and 0.001 < gap10 < 0.01
    # the timeline figure: w = 143/184
    prev, nxt = TEN.coupon_dates(SETTLE)
    assert (nxt[0] - SETTLE).days == 143 and (nxt[0] - prev).days == 184


def test_exercises():
    assert round(2.125 * 41 / 184, 6) == 0.473505
    assert from_32nds("99-16+") == 99.515625 and to_32nds(101.296875) == "101-09+"
    s = D(2026, 9, 25)
    assert round(Bond(4.0, D(2029, 9, 25)).clean_price(0.05, s), 4) == 97.2459
    r2 = Bond(4.0, D(2028, 9, 25)).risk(0.04, s)
    assert (round(r2["macaulay"], 4), round(r2["modified"], 4), round(r2["dv01"] * 1e4, 2)) == (1.9419, 1.9039, 190.39)
    full = TEN.dirty_price(Y10 - 0.01, SETTLE) - R10["dirty"]
    lin = R10["dirty"] * R10["modified"] * 0.01
    quad = lin + 0.5 * R10["dirty"] * R10["convexity"] * 1e-4
    assert (round(full, 4), round(lin, 4), round(quad, 4)) == (8.4403, 8.0444, 8.4268)
    assert round(full - quad, 3) == 0.014 and round(full - lin, 2) == 0.40
    b = Bond(5.0, D(2030, 8, 15))
    a1, a2 = b.accrued(D(2026, 3, 31)), 5 * thirty_360(D(2026, 2, 15), D(2026, 3, 31))
    assert (round(a1, 6), round(a2, 6), round(a2 - a1, 3), round((a2 - a1) * 1e4)) == (0.607735, 0.638889, 0.031, 312)
    dfs = bootstrap_par(PAR)
    assert round(dfs[-1], 6) == 0.657651 and round(2 * (dfs[-1] ** (-1 / 20) - 1) * 100, 4) == 4.2350
    r30 = Bond(4.5, D(2056, 8, 15)).risk(0.045, D(2026, 8, 15))
    assert (round(r30["macaulay"], 2), round(r30["modified"], 2), round(r30["dv01"] * 1e4)) == (16.74, 16.37, 1637)


def test_problem():
    prev, nxt = FIVE.coupon_dates(SETTLE)
    assert prev == D(2026, 3, 31) and nxt[0] == D(2026, 9, 30)
    assert round(FIVE.accrued(SETTLE), 6) == 1.945355 and round(2 * 178 / 183, 6) == 1.945355
    clean5 = FIVE.clean_price(Y5, SETTLE)
    assert round(clean5, 6) == 100.224893 and to_32nds(clean5) == "100-07"
    assert round(FIVE.dirty_price(Y5, SETTLE) * 1e6) == 102_170_249
    assert (round(H["dv01_5_per_m"], 2), round(H["dv01_10_per_m"], 2)) == (451.43, 804.44)
    assert (round(H["conv5"], 2), round(H["conv10"], 2)) == (23.18, 75.82)
    assert round(H["face_short"] / 1e6, 2) == 56.12 and round(H["ratio"], 4) == 0.5612
    assert round(H["face_short"] * TEN.dirty_price(Y10, SETTLE) / 100) == 56_606_398
    assert round(H["net_cash"]) == 45_563_851
    assert round(H["pnl_up1"], 2) == -9.61
    assert (round(H["pnl_up25"]), round(H["pnl_dn25"])) == (-5934, -6092)
    assert (round(H["pnl_5up10"]), round(H["pnl_10up10"])) == (-450_252, 449_295)
    later = D(2026, 10, 23)
    d5 = FIVE.risk(Y5, later)["dv01"] * 1e6
    d10 = TEN.risk(Y10, later)["dv01"] * H["face_short"] / 100
    assert (round(d5), round(d10), round(d5 - d10)) == (44_519, 44_863, -344)


def test_interview():
    z = Bond(0.0, D(2036, 9, 25)).risk(0.05, D(2026, 9, 25))
    c = Bond(5.0, D(2036, 9, 25)).risk(0.05, D(2026, 9, 25))
    assert round(z["dirty"]) == 61 and round(z["dv01"], 3) == 0.060 and round(c["dv01"], 3) == 0.078
    assert round(c["macaulay"]) == 8
    assert round(1 / 0.04) == 25 and round(1.04 / 0.04) == 26
