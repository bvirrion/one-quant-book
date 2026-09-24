"""Numbers gate: every numerical answer printed in Book 6, chapter 24 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_alm as m
from firm_alm import USD_SHOCKS_2024, Position, lcr

E = m.eve_table()
N = m.nii_table()
L = m.lcr_now()
H = m.htm_loss()
Q = m.liquid_same_day()


def test_text():
    assert m.equity_book() == 16.0
    p = m.positions()[2]
    cf = p.cashflows()
    pv = [c / 1.018 ** t for t, c in cf]
    assert round(sum(t * v for (t, _), v in zip(cf, pv, strict=True)) / sum(pv), 1) == 6.3
    assert (round(L["hqla"], 1), round(L["level1"], 1), round(L["level2"], 1)) == (61.0, 36.6, 24.4)
    assert round(L["outflows"], 1) == 65.6 and round(100 * L["lcr"]) == 93
    f = dict(m.ftp_curve())
    assert (f"{f[0.25]:.2f}", f"{f[5]:.2f}", f"{f[10]:.2f}") == ("4.58", "4.84", "4.97")
    assert round(E["base"], 1) == 22.9
    d = E["delta"]
    assert (round(d["parallel_up"], 2), round(d["steepener"], 2), round(d["parallel_down"], 2)) == (-6.95, -4.60, 8.64)
    assert round(100 * E["ratio"]) == 43 and round(0.15 * 16, 1) == 2.4
    assert round(m.bank().delta_eve(USD_SHOCKS_2024)["steepener"], 2) == -6.79
    assert round(N[0.35]["base"], 2) == 4.27
    assert (round(N[0.35]["up200"], 2), round(N[0.80]["up200"], 2)) == (0.49, -1.07)
    assert round(100 * H["pct"], 1) == -19.2 and round(H["loss"], 1) == -17.2 and round(100 * H["of_equity"]) == 108
    assert round(m.afs_loss(), 1) == -3.9
    assert round(Q["liquid"], 1) == 36.1 and round(100 * Q["share"], 1) == 20.9


def test_exercises():
    r = lcr([Position("a", "asset", 30.0, 0.0, 0.0, "cash", hqla="L1"),
             Position("b", "asset", 40.0, 0.0, 0.0, "cash", hqla="L2A")], [(10.0, 1.0)], 0.0)
    assert round(r["hqla"], 6) == 50.0
    assert round(100 * 6.2 * 0.035, 1) == 21.7 and round(300 * math.exp(-5 / 4)) == 86
    assert (round(N[0.35]["up350"], 2), round(N[0.80]["up350"], 2)) == (0.86, -1.87)


def test_problem():
    assert round(16 + H["loss"] + m.afs_loss(), 1) == -5.1
    assert round(40 / (140 / 0.85), 2) == 0.24 and round(140 / 0.85) == 165
