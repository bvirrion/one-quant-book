"""Numbers gate: every numerical answer printed in Book 6, chapter 11 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_inflation as m

CT = {r[0]: r for r in m.convexity_table()}
C = m.caps()
L = m.lpi()


def test_text():
    assert [round(CT[i][3], 1) for i in (1, 4, 10, 19)] == [0.0, -1.8, -15.2, -42.5]
    assert (round(CT[10][1], 2), round(CT[10][2], 2)) == (3.42, 3.27)
    assert (round(C["yoy_swap"] * 100, 2), round(C["zc_swap"] * 100, 2)) == (3.22, 3.28)
    exact, mc, se = m.mc_check()
    assert (round(exact, 5), round(mc, 5), round(se, 5)) == (1.03268, 1.03277, 0.00013)
    assert [round(v, 1) for _, v in m.rho_effect() if _ in (-0.5, 0.0, 0.5)] == [-20.6, -16.4, -12.2]
    s = m.us_seasonals()
    assert [round(s[k], 2) for k in (1, 2, 3, 11, 12)] == [0.18, 0.26, 0.31, -0.36, -0.35]
    p = m.seasonal_forward_path()
    assert (round(p[5][2] - p[5][1], 1), round(p[6][2] - p[6][1], 1)) == (1.0, 1.1)
    assert (round(C["cap"] * 1e4, 1), round(C["floor"] * 1e4, 1)) == (181.1, 45.8)


def test_exercises():
    assert round(m.NOMINAL.df_t(10), 4) == 0.6771
    assert (round(m.NOMINAL.df_t(10) * 1.0328**10, 4), round(1.0328**10, 4)) == (0.9349, 1.3809)
    base = m.model().lpi_leg(20, 0.05, 0.0)["lpi"]
    assert round(m.model(sigma_i=0.025).lpi_leg(20, 0.05, 0.0)["lpi"] - base, 4) == -0.0182
    assert round(m.model(sigma_r=0.009).lpi_leg(20, 0.05, 0.0)["lpi"] - base, 4) == -0.0061


def test_problem():
    f, t = L["five"], L["two_half"]
    assert (round(f["uncapped"], 4), round(f["uncapped_exact"], 4), round(f["lpi"], 4), round(t["lpi"], 4)) == (
        0.8356, 0.8345, 0.7863, 0.6371)
