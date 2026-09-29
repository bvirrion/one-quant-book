"""Numbers gate: every number printed in Book 14, chapter 11 (text and solutions)."""
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_europe as e  # noqa: E402

g = e.gm


def r(x, n=1):
    return round(x, n)


def test_pairs_table():
    rows = {(p["a"], p["b"]): p for p in e.pair_rows()}
    expect = {("ld4", "fr2"): (677.7, 2260.6, 3305.0), ("ld4", "bergamo"): (992.2, 3309.7, 4838.7),
              ("fr2", "bergamo"): (497.6, 1659.9, 2426.8), ("ld4", "basildon"): (77.4, 258.0, 377.2),
              ("docklands", "basildon"): (34.0, 113.5, 166.0), ("ld4", "docklands"): (44.0, 146.9, 214.8),
              ("basildon", "fr2"): (603.2, 2012.2, 2941.8), ("basildon", "bergamo"): (936.2, 3122.9, 4565.7),
              ("fr2", "zh4"): (306.7, 1023.1, 1495.8), ("zh4", "bergamo"): (204.5, 682.2, 997.4),
              ("fr2", "vasby"): (1195.0, 3986.0, 5827.6), ("ld4", "vasby"): (1462.5, 4878.2, 7132.0)}
    for k, v in expect.items():
        p = rows[k]
        assert (r(p["km"]), r(p["vacuum_us"]), r(p["fibre_us"])) == v, k
    assert (round(rows[("ld4", "docklands")]["vacuum_us"]), round(rows[("docklands", "basildon")]["vacuum_us"])) == (147, 114)


def test_migration():
    m = {x["from"]: x for x in e.migration()}
    ld4 = m["ld4"]
    assert (round(ld4["vac_before"]), round(ld4["vac_after"]), round(ld4["fib_before"]), round(ld4["fib_after"])) == \
        (258, 3310, 377, 4839)
    assert (round(ld4["vac_after"] - ld4["vac_before"]), round(ld4["fib_after"] - ld4["fib_before"])) == (3052, 4461)
    assert (r((ld4["vac_after"] - ld4["vac_before"]) / 1e3, 2), r((ld4["fib_after"] - ld4["fib_before"]) / 1e3, 2)) == (3.05, 4.46)
    fr2 = m["fr2"]
    assert round(fr2["vac_before"] - fr2["vac_after"]) == 352 and (r(fr2["vac_before"] / 1e3, 2), r(fr2["vac_after"] / 1e3, 2)) == (2.01, 1.66)
    assert round(fr2["fib_before"] - fr2["fib_after"]) == 515
    assert r((m["zh4"]["vac_before"] - m["zh4"]["vac_after"]) / 1e3, 2) == 1.81
    assert (r(m["docklands"]["vac_after"] / 1e3, 1), r(e.gm.floor_us(e.distance("basildon", "bergamo")) / 1e3, 1)) == (3.2, 3.1)
    reg = e.registry()
    assert reg.moves("XPAR") == [("2022-06-06", "basildon", "bergamo")]


def test_triangle_and_routes():
    before = [round(x[2]) for x in e.triangle(e.BEFORE)]
    after = [round(x[2]) for x in e.triangle(e.AFTER)]
    assert before == [678, 603, 77] and after == [678, 498, 992]
    assert (678 + 992, round(306.7 + 204.5)) == (1670, 511)
    d = e.distance
    slough = d("fr2", "ld4") + d("ld4", "bergamo")
    zur = d("fr2", "zh4") + d("zh4", "bergamo")
    assert (r(g.floor_us(slough) / 1e3, 2), r(g.floor_us(zur) / 1e3, 2), r(g.floor_us(d("fr2", "bergamo")) / 1e3, 2)) == \
        (5.57, 1.71, 1.66)
    assert (r((zur - d("fr2", "bergamo")) / 1e3), round(g.floor_us(zur - d("fr2", "bergamo")))) == (13.6, 45)
    assert r((g.floor_us(slough) - g.floor_us(d("fr2", "bergamo"))) / 1e3) == 3.9
    rr = {x["label"]: x for x in e.route_rows()}
    mk, ew = rr["McKay 2015 LD4-FR2"], rr["EWIN 2024 LD4-IT3"]
    assert (round(mk["floor_us"] / 1e3, 3), round(mk["factor"], 3), round(mk["published_us"] - mk["floor_us"])) == (2.261, 1.026, 59)
    assert round(mk["fibre_us"] / 1e3, 3) == 3.305 and round(mk["fibre_us"] - 2320) == 985
    assert (round(ew["floor_us"] / 1e3, 3), round(ew["factor"], 2), round(ew["fibre_us"] / 1e3, 3)) == (3.311, 1.21, 4.839)
    assert (round(4000 - ew["floor_us"]), round(ew["fibre_us"] - 4000)) == (689, 839)
    assert round(1.2 * ew["fibre_us"]) == 5806 and round(1.2 * ew["fibre_us"] - 4000) == 1806


def test_registry_views():
    reg = e.registry()
    assert reg.primary("XEUR") == "fr2" and reg.primary("XSWX") == "zh4" and reg.primary("XSTO") == "vasby"
    near = e.nearest_from("ld4")
    assert [x["site"] for x in near] == ["docklands", "basildon", "fr2", "zh4", "bergamo", "vasby"]
    with pytest.raises(LookupError):
        reg.primary("XMIL")


def test_small_runs():
    pts = dict((i, (x, y)) for i, x, y in e.map_points("eu"))
    assert pts["ld4"][0] < pts["fr2"][0] and pts["bergamo"][1] < pts["zh4"][1] < pts["fr2"][1]
