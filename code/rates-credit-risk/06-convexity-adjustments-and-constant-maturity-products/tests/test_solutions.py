"""Numbers gate: every numerical answer printed in Book 6, chapter 6 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_cms as m
from firm_cms import cms_caplet, cms_rate, timing_adjustment_normal
from firm_multicurve import add_months
from firm_normalvol import bachelier

TAB = m.cms_table()
ST = m.steepener()


def test_text():
    assert round(timing_adjustment_normal(0.03, 0.5, 5.0, 0.0075) * 1e4, 2) == 1.39
    assert [round(r[2], 2) for r in TAB] == [1.39, 3.49, 5.87, 11.73, 17.40, 26.58]
    assert [round(r[3], 2) for r in TAB] == [1.62, 4.46, 7.92, 15.51, 22.91, 32.14]
    assert (round(TAB[-1][1], 3), round(TAB[-1][1] + TAB[-1][3] / 100, 3)) == (3.051, 3.372)
    ratios = [r[3] / r[2] for r in TAB]
    assert (round(min(ratios) - 1, 2), round(max(ratios) - 1, 2)) == (0.16, 0.35)
    s = m.setup(5.0)
    sm = m.smile(5.0)
    c = cms_caplet(0.035, s["fwd"], s["t"], s["annuity"], s["df_pay"], s["accruals"], sm)
    naive = s["df_pay"] * bachelier(s["fwd"], 0.035, s["t"], sm(0.035))
    assert (round(s["fwd"] * 100, 3), round(sm(0.035) * 1e4, 1), round(c * 1e4, 1), round(naive * 1e4, 1)) == (
        3.098, 75.9, 48.5, 43.0)
    assert round((c / naive - 1) * 100) == 13
    assert round(m.quanto_example() * 1e4, 1) == -9.0
    assert round(ST["rho"], 3) == 0.769 and round(ST["first_spread_vol"] * 1e4, 1) == 45.1


def test_exercises():
    assert round(0.25 * 0.008**2 * 4 / (1 + 0.25 * 0.025) * 1e4, 2) == 0.64
    assert round(1 / (10 * 1.0139), 5) == 0.09863
    assert round(11.73 * 1.2**2, 2) == 16.89
    rows = m.replication_contributions()
    tot = sum(c for _, c in rows)
    assert round(sum(c for k, c in rows if abs(k - 3.051) > 2) / tot * 100) == 29
    s = m.setup(5.0)
    dfp = m.DISC.df(add_months(m.SPOT, 180))
    assert round((cms_rate(s["fwd"], s["t"], s["annuity"], dfp, s["accruals"], m.smile(5.0), m.LO) - s["fwd"]) * 1e4,
                 2) == -19.24


def test_problem():
    assert (round(ST["fixed_leg"], 5), round(ST["unit_leg"], 5), round(ST["participation"], 2)) == (
        0.17118, 0.05785, 2.96)
    assert [round(m.steepener(r)["participation"], 2) for r in (0.6, 0.8, 0.95)] == [2.44, 3.10, 4.47]
