"""Numbers gate: every number printed in Book 14, chapter 13 (text and solutions)."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_fibre as n  # noqa: E402

fr, gm = n.fr, n.gm


def r(x, k=1):
    return round(x, k)


def test_light_in_glass():
    assert r(3 / 0.16) == 18.8 and round(30 / 0.16) == 188 and r(0.16 * 80, 1) == 12.8
    assert r(100 * 10 ** (-0.16 * 80 / 10), 1) == 5.2
    assert round(0.16 * 1359) == 217 and round(18 * 1359 / 1000) == 24
    assert r(1 - 1.003 / 1.462, 2) == 0.31 and r(100 * (1.462 - 1), 0) == 46


def test_published_table():
    p = {x["label"]: x for x in n.published()}
    a, b, c = p["Chicago-New Jersey fibre, 2010"], p["Chicago-New Jersey fibre, later"], p["New York-London subsea, 2015"]
    assert (r(a["geodesic_km"]), r(a["floor_us"] / 1e3, 3), round(a["path_km"]), r(a["factor"], 3)) == (1129.2, 5.507, 1359, 1.204)
    assert (round(b["path_km"]), r(b["factor"], 3), round(a["path_km"]) - round(b["path_km"])) == (1339, 1.185, 20)
    assert (r(c["geodesic_km"]), r(c["published_us"] / 1e3, 3), r(c["floor_us"] / 1e3, 3), round(c["path_km"], -1)) == \
        (5551.0, 29.475, 27.070, 6040)
    assert r(c["factor"], 3) == 1.088 and r(c["factor"], 2) == 1.09 and round(c["path_km"]) == 6038
    assert r(a["equipment_us"]) == 21.7 and round(a["published_us"] - a["floor_us"]) == 1143 and round(a["excess_km"]) == 230
    assert r(100 * a["equipment_us"] / (a["published_us"] - a["floor_us"])) == 1.9
    assert round(1e-6 * fr.C0 / 1.462) == 205
    assert r(2 * a["floor_us"] / 1e3, 3) == 11.014 and r(gm.floor_us(a["geodesic_km"] * 1e3) / 1e3, 3) == 3.767


def test_variants_and_sensitivity():
    v = {k: c["total"] for k, c in n.variants().items()}
    assert (r(v["as inverted"] / 1e3, 3), r(v["with a DCF spool"] / 1e3, 3)) == (6.650, 7.976)
    assert (r(v["hollow-core on the same path"] / 1e3, 3), r(v["standard fibre on the geodesic"] / 1e3, 3)) == (4.569, 5.528)
    assert r((v["as inverted"] - v["hollow-core on the same path"]) / 1e3, 2) == 2.08
    assert r((v["with a DCF spool"] - v["as inverted"]) / 1e3, 2) == 1.33
    assert r((v["as inverted"] - v["standard fibre on the geodesic"]) / 1e3, 2) == 1.12
    c = n.variants()["as inverted"]
    assert (r(2 * c["glass"] / 1e3, 2), r(2 * c["path"] / 1e3, 2), r(2 * (c["amps"] + c["terminals"]) / 1e3, 2)) == (11.01, 2.24, 0.04)
    s = dict(n.sensitivity())
    assert (r(s[0], 3), r(s[200], 3)) == (1.208, 1.171) and round(100 * (s[200] - 1)) == 17
    inv = fr.invert(6650, n.geodesic_km("cermak", "carteret"), equipment_us=200)
    assert (round(inv["path_km"]), round(inv["excess_km"]), round(inv["excess_km"] * 1.462 / fr.C0 * 1e9)) == (1323, 193, 943)
    assert r((4569.0 - 3982) / 1e3, 2) == 0.59 and r((6650 - 3982) / 1e3, 2) == 2.67


def test_costs_and_exercise():
    q = n.PRICES
    assert fr.dark(q["iru"], q["iru_years"], q["om_year"], q["capex"], q["capex_years"]) == 675_000
    assert fr.lit(q["lit_monthly"]) == 1_080_000
    assert r(fr.break_even_years(q["iru"], q["om_year"], q["capex"], q["lit_monthly"]), 1) == 9.6
    g = n.geodesic_km("cermak", "carteret")
    mw = 1.011 * gm.floor_us(g * 1e3, "air")
    hc = g * 1.003 / fr.C0 * 1e9
    assert (round(mw), round(hc), r((mw - 21.7) / hc, 4), r(mw / hc, 3)) == (3809, 3778, 1.0025, 1.008)
    assert r(1.03 * 1.462, 2) == 1.51


def test_small_runs():
    rt = fr.build("x", 300.0, 1.1, terminal_us=5.0)
    assert fr.components(rt)["total"] > fr.components(fr.with_index(rt, 1.003))["total"]
    assert len(n.costs(5)) == 6
