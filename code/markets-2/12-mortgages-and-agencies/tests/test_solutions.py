"""Numbers gate: every numerical answer printed in Book 2, Chapter 12 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/prepay"))
from firm_prepay import level_payment, psa_cpr, refi_cpr, smm
from mbs_demo import (
    FACE,
    Y0,
    convexity_hedge,
    mbs_price,
    new_pool,
    price_yield,
    risk_table,
    roll_example,
    speed_at,
    static_price,
    wal_table,
)

R = risk_table()
H = convexity_hedge()
ROLL = roll_example()


def test_text():
    assert round(level_payment(FACE, 0.065 / 12, 360)) == 632_068
    f = new_pool()[0]
    assert (round(f.interest), round(f.scheduled), round(f.prepaid)) == (500_000, 90_401, 16_667)
    assert round(FACE * 0.065 / 12) == 541_667 and round(f.scheduled + f.prepaid) == 107_068
    w = wal_table()
    assert (round(w[0.0], 1), round(w[1.0], 1), round(w[3.0], 1)) == (19.6, 11.5, 5.8)
    assert (round(refi_cpr(-1), 2), round(refi_cpr(1), 2), round(speed_at(Y0) * 100, 1)) == (0.06, 0.5, 11.9)
    assert round(ROLL["paydown"] * 100, 2) == 1.16 and round(ROLL["rate"] * 100, 2) == 2.95
    assert round(ROLL["drop_at_repo"], 2) == 0.16
    up, dn = mbs_price(Y0 + 0.01), mbs_price(Y0 - 0.01)
    assert (round(dn - 100, 2), round(100 - up, 2)) == (2.07, 6.11)
    assert (round(static_price(Y0 - 0.01) - 100, 2), round(100 - static_price(Y0 + 0.01), 2)) == (5.04, 4.60)


def test_exercises():
    assert [round(100 * x, 1) for x in (psa_cpr(10), psa_cpr(20, 1.5), psa_cpr(40, 2.0))] == [2.0, 6.0, 12.0]
    assert round(smm(0.06) * 100, 4) == 0.5143 and round(50e6 * smm(0.06)) == 257_151
    assert round(ROLL["rate_no_drop"] * 100, 2) == 5.90
    rows = {round(y, 2): (m, s) for y, m, s in price_yield()}
    assert (round(rows[4.0][0], 2), round(rows[4.0][1], 2)) == (102.88, 110.58)
    assert round(refi_cpr(0.02) * 100) == 48
    got = [(round(R[y]["duration"], 2), round(R[y]["convexity"])) for y in (0.055, 0.060, 0.065)]
    assert got == [(1.77, -478), (4.73, -560), (6.51, -93)]
    assert [round(v, 2) for v in wal_table().values()] == [19.62, 14.73, 11.49, 7.73, 5.77]


def test_problem():
    assert (round(R[0.06]["cpr"] * 100, 1), round(R[0.06]["price"], 2), round(H["d0"], 2)) == (11.9, 100.0, 4.73)
    assert round(H["dv0"] / 1e6, 2) == 4.73 and round(H["swap_dv01_100m"]) == 73_601
    assert round(H["dv0"] / H["swap_dv01_100m"] * 100e6 / 1e9, 2) == 6.42
    assert (round(R[0.055]["cpr"] * 100, 1), round(H["p1"], 2), round(H["d1"], 2)) == (21.3, 101.61, 1.77)
    assert round(H["dv1"] / 1e6, 2) == 1.80 and round(H["lost"] / 1e6, 2) == 2.93
    assert round(H["receive"] / 1e9, 2) == 3.97 and round(H["receive"] / 1e9, 1) == 4.0
    assert round(R[0.065]["duration"], 2) == 6.51
    assert round(H["receive"] / H["market_2003"] * 100, 1) == 1.4
