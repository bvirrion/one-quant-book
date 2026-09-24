"""Numbers gate: every numerical answer printed in Book 6, chapter 27 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_pnlexplain as m
from firm_pnlexplain import ipv

D = m.day()
R = m.revaluation()
IPV = m.ipv_table()
AVA = m.ava_table()


def test_text():
    g = D["greeks"]
    assert round(g["delta"] * 1e-4) == 139_103 and round(g["vanna"] * 1e-8) == 1_086
    assert round(D["actual"]) == 4_571_501 and round(D["desk"]["explained"]) == 4_173_095
    assert round(D["unexplained_desk"]) == 398_406 and round(100 * D["unexplained_desk"] / D["actual"]) == 9
    assert round(D["full"]["vanna"]) == 391_087 and round(D["unexplained_full"]) == 7_319
    f, s = R["f_first"], R["s_first"]
    assert (round(f["f"]), round(f["s"]), round(f["t"])) == (4_240_447, 336_046, -4_992)
    assert (round(s["s"]), round(s["f"])) == (0, 4_576_493)
    assert IPV[0]["adj_vol"] == 0.0 and round(1e4 * IPV[1]["verified"]) == 93 and round(IPV[1]["adj_value"]) == 146_482
    assert [round(x) for x in AVA["individual"]] == [190_578, 232_964] and round(AVA["total"]) == 211_771
    assert round(AVA["fv_abs"] / 1e6, 2) == 6.87 and round(AVA["simplified"]) == 6_872


def test_exercises():
    assert ipv([38.0], [35.0], [2.0]) == [(37.0, -1.0)]
    u = dict((a, b) for a, b, _ in m.unexplained_by_move())
    assert round(u[15.0] / 1e3) == 181
    old = m.DISPERSION
    m.DISPERSION = [2 * x for x in old]
    try:
        a = m.ava_table()
    finally:
        m.DISPERSION = old
    assert [round(x) for x in a["individual"]] == [382_470, 468_316] and round(a["total"]) == 425_393


def test_problem():
    assert round(1086.35 * 30 * 12) == 391_086 and round(D["greeks"]["vanna"] * 1e-8 * 30 * 12) == 391_087
