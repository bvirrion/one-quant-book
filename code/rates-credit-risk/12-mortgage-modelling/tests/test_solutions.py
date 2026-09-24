"""Numbers gate: every numerical answer printed in Book 6, chapter 12 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_mbs as m
from firm_mbsoas import simulate_paths

B = m.base()
E = m.convexity_event()


def test_text():
    _, p10 = simulate_paths(m.CURVE, m.KAPPA, m.SIGMA, 1, 2)
    assert round(p10[0, 0] * 100, 2) == 3.80
    assert (round(B["oas"] * 1e4), round(B["zv_spread"] * 1e4), round(B["option_cost"] * 1e4)) == (146, 181, 34)
    assert (round(B["duration"], 2), round(B["convexity"]), round(B["wal"], 1)) == (4.99, -123, 6.4)
    assert round(m.no_burnout(B["oas"]), 2) == 99.20
    assert (round(B["io"], 2), round(B["po"], 2), round(B["io_up"], 2), round(B["po_up"], 2)) == (
        25.26, 74.74, 26.61, 72.10)
    assert (round(E["d1"]["value"], 2), round(E["d1"]["duration"], 2)) == (94.50, 6.17)
    assert (round(E["dv01_before"] / 1e6, 2), round(E["dv01_after"] / 1e6, 2)) == (4.99, 5.83)
    assert round(E["swap_dv01"]) == 796_282 and round(E["notional"] / 1e9, 2) == 1.06


def test_exercises():
    assert round((0.060 - (0.0380 + 0.0175)) * 100, 2) == 0.45
    t = dict(m.price_rate_table(B["oas"]))
    assert (round(t[-100] - 100, 2), round(t[100] - 100, 2)) == (4.54, -5.50)


def test_problem():
    assert (round(B["io_dn"], 2), round(B["po_dn"], 2)) == (24.00, 77.21)
    assert round(E["extra"]) == 844_025
