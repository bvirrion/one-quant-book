"""Numbers gate: every numerical answer printed in Book 5, Chapter 21 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_convertible import (
    LAM0,
    call_effect,
    credit_sensitivity,
    greeks,
    grid,
    profile,
    rpv01,
    stress,
    table,
    value_at,
)

T = table()


def row(model, s):
    return next(r for r in T[model] if r["s"] == s)


def test_profiles():
    c = [round(row("constant", s)["value"], 1) for s in (20, 30, 40, 60, 80)]
    assert c == [89.1, 100.2, 116.0, 156.7, 203.2]
    assert round(row("constant", 30)["floor"], 1) == 83.2
    assert [round(100 * row("constant", s)["premium"], 1) for s in (20, 30, 40, 60, 80)] == [78.2, 33.7, 16.0, 4.5, 1.6]
    assert (round(row("constant", 20)["delta"], 2), round(row("constant", 80)["delta"], 2)) == (0.84, 2.39)
    e = {s: row("e2c", s) for s in (20, 30, 80)}
    assert (round(e[20]["value"], 1), round(e[30]["value"], 1), round(e[20]["floor"], 1), round(e[80]["floor"], 1)) == (83.9, 98.5, 78.1, 90.4)
    assert (round(e[30]["delta"], 2), round(row("constant", 30)["delta"], 2), round(e[20]["delta"], 2)) == (1.55, 1.37, 1.39)
    from dv_convertible import grid as _g
    from firm_convertible import greeks as _gr
    assert [round(_gr(x, _g(), 0.03)["gamma"], 2) for x in (15, 10)] == [-0.03, -0.10] and _gr(19.5, _g(), 0.03)["gamma"] > 0
    assert (round(e[30]["value"], 2), round(e[30]["floor"], 2), round(100 * e[30]["premium"], 1)) == (98.47, 82.91, 31.3)
    p = profile()
    i10 = list(p["s"]).index(10.0)
    assert (round(p["cb"][i10]), round(p["floor"][i10])) == (69, 68) and round(p["cb"][i10], 2) == 69.07
    i80 = list(p["s"]).index(80.0)
    assert round(p["cb"][i80]) == 202
    assert round(100 * LAM0 * (10 / 30) ** (-1.2), 1) == 18.7 and round(100 * LAM0 * (80 / 30) ** (-1.2), 1) == 1.5


def test_call_and_credit():
    ce = {s: (a, b) for s, a, b in call_effect()}
    assert (round(ce[40][0], 1), round(ce[40][1], 1), round(ce[52][0], 1), round(ce[52][1], 1)) == (115.3, 119.2, 138.6, 143.3)
    assert (round(ce[40][1] - ce[40][0], 1), round(ce[52][1] - ce[52][0], 2)) == (3.9, 4.65)
    cs = credit_sensitivity()
    assert (round(-cs["cs01"], 4), round(-cs["floor_cs01"], 4)) == (0.0167, 0.0296)
    assert round(rpv01(LAM0), 2) == 4.12


def test_stress():
    s = stress()
    assert (round(s["v0"], 2), round(s["v1"], 2), round(s["unhedged"], 2), round(s["hedged"], 2)) == (98.47, 86.62, -11.84, -2.55)
    assert round(s["delta"] * 6, 2) == 9.30 and round(s["lam_target"], 3) == 0.10
    assert (round(s["cds_notional"], 1), round(s["cds_pnl"], 2), round(s["with_cds"], 2)) == (40.6, 4.47, 1.93)
    c = stress(p=0.0)
    assert (round(c["delta"], 2), round(c["hedged"], 2)) == (1.37, -4.38)
    assert round(stress(0.0, 300.0)["hedged"], 2) == -3.35 and round(stress(-0.2, 0.0)["hedged"], 2) == 2.21
    assert round(c["hedged"] - s["hedged"], 2) == -1.83


def test_exercises():
    assert (100 / 2.5, 2.5 * 36, round(100 * (110 / 90 - 1), 1)) == (40.0, 90.0, 22.2)
    s2 = stress(p=2.0)
    assert (round(s2["delta"], 2), round(s2["hedged"], 2), round(s2["v0"], 2), round(s2["v1"], 2)) == (1.65, -1.25, 97.32, 86.18)
    assert round(greeks(30, grid(LAM0, 1.2))["delta"] - greeks(30, grid(LAM0, 0.0))["delta"], 2) == 0.18
    assert abs(value_at(30, grid()) - 98.465) < 1e-2
