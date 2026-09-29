"""Numbers gate: every numerical answer printed in Book 17, chapter 3 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_options as o  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


def test_graph():
    g = o.graph()
    assert len(g.firms()) == 6 and g.by_decade() == {1980: 4, 1990: 1, 2000: 1}
    assert len(g.edges) == 3 and len(g.unsourced()) == 4 - 1
    assert sorted(e.src for e in g.edges) == ["Belvedere Trading", "IMC", "Susquehanna"]
    assert g.by_place()["Amsterdam"] == ["IMC", "Optiver"]
    assert r(100 * 3 / 6, 0) == 50


def test_results_metrics():
    m = o.metrics()
    rs = o.results()
    assert r(100 * rs[0]["net_profit"] / rs[0]["net_trading_income"]) == 41.8
    assert (r(100 * m[2024]["nti_growth"]), r(100 * m[2025]["nti_growth"])) == (26.0, 30.4)
    assert (r(100 * m[2024]["profit_growth"]), r(100 * m[2025]["profit_growth"])) == (18.2, 29.2)
    assert (r(100 * m[2024]["margin"]), r(100 * m[2025]["margin"])) == (39.2, 38.8)
    assert (r(100 * m[2024]["roe"]), r(100 * m[2025]["roe"])) == (30.4, 34.0)
    assert (r(m[2024]["nti_per_head_max"], 2), r(m[2025]["nti_per_head_max"], 2)) == (1.66, 2.28)
    assert (r(4556 / 2400, 2), r(4556 / 2500, 2)) == (1.90, 1.82)
    assert [r(x["net_trading_income"] / 1000) for x in rs] == [2.8, 3.5, 4.6]


def test_counts():
    assert 20 * 50 * 2 == 2000 and 15 * 40 * 2 == 1200 and 12 * 30 * 2 * 2 == 1440
    assert 120 * 100 * 2000 == 24_000_000
    assert r(1.29 / 1.12, 2) == 1.15


def test_options_pay():
    p = o.options_pay()
    a, b = p[("all", "options houses")], p[("all", "other market makers")]
    assert (a["n"], a["employers"], a["p50"], a["p10"], a["p90"]) == (130, 3, 150_000, 84_800, 200_000)
    assert (b["n"], b["employers"], b["p50"], b["p10"], b["p90"]) == (237, 7, 200_000, 130_000, 300_000)
    assert (a["diff"], a["diff_lo"], a["diff_hi"]) == (-50_000, -53_900, -35_000)
    assert [p[(r, "options houses")]["p50"] for r in ("quant researcher", "software engineer", "trader")] == [
        150_000, 146_100, 200_000]
    assert [p[(r, "other market makers")]["p50"] for r in ("quant researcher", "software engineer", "trader")] == [
        200_000, 190_000, 192_500]
    assert p[("quant researcher", "options houses")]["diff"] == -50_000
    assert p[("software engineer", "options houses")]["diff"] == -43_900
    import csv
    with open(o.DATA / "lca_options_levels.csv") as f:
        lv = {(r["group"], r["level"]): int(r["n"]) for r in csv.DictReader(f)}
    assert (lv[("options houses", "I")], lv[("other market makers", "I")]) == (23, 8)
    assert (round(100 * 23 / 130, 1), round(100 * 8 / 237, 1)) == (17.7, 3.4)
