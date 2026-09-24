"""Numbers gate: every numerical answer printed in Book 6, chapter 19 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_xvafund as m
from firm_xvafund import IrTrade, ir_addon, sa_ccr_ead, supervisory_duration

A = m.adjustments()
B = m.adjustments(csa=True, with_im=True)
C = m.adjustments(csa=True)
E = m.ead_today()
CAP = m.capital_profile()


def test_text():
    assert round(100 * m.swap_rate(), 2) == 3.80
    assert (round(A["fca"]), round(A["fba"]), round(A["fva"])) == (127_400, 185_797, -58_397)
    assert round(m.running_equivalent(A["fca"]), 1) == 1.5 and round(B["fca"]) == 3_102
    assert round(m.im_today() / 1e6, 2) == 4.22 and round(B["mva"]) == 175_217
    assert round(E["sd"], 2) == 7.87 and round(E["addon"] / 1e6, 2) == 3.93 and round(E["ead"] / 1e6, 2) == 5.51
    assert round(1.5 * math.sqrt(10 / 250), 2) == 0.30 and round(E["ead_csa"] / 1e6, 2) == 2.35
    assert (round(CAP["ccr"][0]), round(CAP["cva"][0])) == (440_686, 368_944)
    k = int(CAP["total"].argmax())
    assert round(CAP["total"][k] / 1e6, 2) == 1.18 and CAP["t"][k] == 1.25
    assert round(A["kva"]) == 558_718
    assert (round(A["cva"]), round(A["dva"]), round(A["total"])) == (272_251, 210_351, 562_220)
    assert round(A["bp"], 1) == 6.8
    assert (round(B["cva"]), round(B["dva"]), round(B["fba"]), round(B["kva"]), round(B["total"])) == (
        33_814, 17_745, 3_367, 156_573, 347_595)
    assert round(B["bp"], 1) == 4.2


def test_exercises():
    assert round(0.006 * 5e6 * 4) == 120_000
    a = ir_addon([IrTrade("USD", 50e6, 0, 5, -1, 5)])
    assert round(supervisory_duration(0, 5), 2) == 4.42 and round(a / 1e6, 3) == 1.106
    assert round(sa_ccr_ead(0, a) / 1e6, 2) == 1.55
    f = dict((s, (u, c)) for s, u, c in m.funding_sensitivity((40, 120)))
    assert (round(f[40][0] * 1e3), round(f[120][0] * 1e3), round(f[40][1] * 1e3), round(f[120][1] * 1e3)) == (
        63_700, 191_101, 1_551, 4_654)


def test_problem():
    assert round(1 - B["fca"] / A["fca"], 2) == 0.98
    assert round(1 - B["kva"] / A["kva"], 2) == 0.72 and round(1 - B["cva"] / A["cva"], 2) == 0.88
    assert round(A["bp"] - B["bp"], 1) == 2.6 and round(A["bp"] - C["bp"], 1) == 4.7
    assert round(C["total"]) == 172_378 and round(C["bp"], 1) == 2.1


def test_effective_maturity():
    from firm_xvafund import effective_maturity
    assert effective_maturity(10.0) == 5.5
