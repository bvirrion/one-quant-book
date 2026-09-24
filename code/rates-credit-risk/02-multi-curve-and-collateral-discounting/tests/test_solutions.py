"""Numbers gate: every numerical answer printed in Book 6, chapter 2 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_multicurve as m
from firm_multicurve import ShiftedCurve, ibor_swap_pv

FWD = m.forward_table(0.25)
CMP = m.discounting_comparison()
CH = m.collateral_choice()
SW = m.switch_value(20, 0.015, 5e8)


def test_text():
    assert (round(FWD[0][3], 1), round(dict((r[0], r[3]) for r in FWD)[10.0], 1)) == (21.6, 11.8)
    assert round(FWD[-1][3]) == 9
    assert (round(CMP["ois"]), round(CMP["single"])) == (7_135_408, 7_075_108)
    assert round(CMP["ois"] - CMP["single"], -2) == 60_300
    assert round(CMP["par_multi"] * 100, 4) == round(CMP["par_single"] * 100, 4) == 2.70
    assert (round(CH["usd_only"]), round(CH["choice"])) == (68_598_292, 68_213_510)
    assert round(CH["usd_only"] - CH["choice"]) == 384_782
    assert round(56.25 / 10, 1) == 5.6
    assert -15 + 20 * 7.5 / 10 == 0


def test_exercises():
    assert round((0.0270 - 0.0255) * 1e4) == 15
    integral = sum(max(0.0, -m.xccy_basis((k + 0.5) / 3650)) for k in range(36500)) / 3650
    assert round(integral * 1e4, 2) == 56.25
    assert round(CH["usd_only"] * (1 - math.exp(-integral))) == 384_782
    pay = m.switch_value(10, 0.015, 1e8, payer=True)
    assert round(pay["change"]) == -73_738 and round(pay["compensation"]) == 73_738
    assert round(dict((r[0], r[3]) for r in FWD)[10.0], 2) == 11.76


def test_problem():
    estr, eonia, _ = m.curves_2020()
    assert round(m.IRS_2020[7] * 100, 2) == 0.08
    assert (round(SW["before"]), round(SW["after"])) == (145_577_447, 146_774_873)
    assert round(SW["change"]) == 1_197_426
    assert round(math.exp(0.00085 * 20), 4) == 1.0171
    from firm_multicurve import Fixing, IborSwap, add_months, calibrate_projection
    ins = [Fixing(m.SWITCH, add_months(m.SWITCH, 6), m.FIX6M_2020)] + [
        IborSwap(m.SWITCH, n, r) for n, r in zip(m.YEARS, m.IRS_2020, strict=True)]
    proj = calibrate_projection(m.SWITCH, eonia, ins)
    base = ibor_swap_pv(proj, estr, m.SWITCH, 20, 0.015, 5e8, payer=False)
    up = ibor_swap_pv(proj, ShiftedCurve(estr, 1e-4), m.SWITCH, 20, 0.015, 5e8, payer=False)
    assert round(up - base) == -141_575
    t = {n: c for n, _, c in m.switch_table()}
    assert round(t[30] / t[15], 1) == 4.1
