"""Numbers gate: every numerical answer printed in Book 17, chapter 20 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_engineer as a  # noqa: E402

fr = a.fr


def r(x, d=2):
    return round(float(x), d)


def test_scale_and_budget():
    s = a.scale()
    assert (round(s["rd_per_virtu"]), round(s["msft_per_virtu"])) == (75, 217)
    hours = 6.5 * 252
    assert hours == 1638 and r(0.001 * 8760 * 60, 1) == 525.6 and r(0.001 * hours * 60, 1) == 98.3
    assert r(0.0001 * hours * 60, 1) == 9.8 and r(0.0005 * hours * 60, 1) == 49.1


def test_cells_and_gaps():
    c = a.cells()
    want = {"systematic fund": (207_000, 67, 6), "multi-manager platform": (200_000, 35, 3),
            "market maker": (175_000, 153, 9), "bank": (155_688, 4790, 8), "exchange": (147_900, 296, 4)}
    assert {k: (c[k]["p50"], c[k]["n"], c[k]["employers"]) for k in want} == want
    assert c["market maker"]["p90"] == 295_000 and max(v["p90"] for v in c.values()) == 295_000
    g = a.kind_gaps()

    def t(fy, o, lv):
        x = g[(fy, o, lv)]
        return r(x["ratio"]), r(x["ratio_lo"]), r(x["ratio_hi"])

    assert t(2025, "bank", "all") == (1.19, 1.16, 1.23) and t(2025, "bank", "II") == (1.25, 1.14, 1.38)
    assert t(2025, "bank", "III") == (1.18, 1.12, 1.27) and t(2025, "bank", "IV") == (1.17, 1.11, 1.29)
    assert t(2025, "bank", "I") == (1.14, 0.78, 1.43) and t(2021, "bank", "all") == (1.32, 1.28, 1.40)
    assert r(g[(2025, "exchange", "all")]["ratio"]) == 1.25 and r(g[(2025, "exchange", "IV")]["ratio"]) == 1.30
    assert (g[(2021, "bank", "all")]["median_trading"], g[(2021, "bank", "all")]["median_other"]) == (165_000, 125_000)
    assert (g[(2025, "bank", "all")]["median_trading"], g[(2025, "bank", "all")]["median_other"]) == (185_000, 155_688)
    assert r(100 * (185_000 / 165_000 - 1), 1) == 12.1 and r(100 * (155_688 / 125_000 - 1), 1) == 24.6
    x = g[(2025, "exchange", "II")], g[(2025, "exchange", "IV")]
    assert (x[0]["median_trading"], x[0]["median_other"], x[1]["median_trading"], x[1]["median_other"]) == (
        175_000, 105_300, 195_000, 149_800)


def test_survey():
    s = a.survey()
    assert [int(s["523000"][q]) for q in a.Q] == [104_600, 132_650, 163_290, 203_840, 245_380]
    assert [int(s[k]["p50"]) for k in ("519200", "513200", "518200", "5220A1", "541500")] == [
        213_520, 164_550, 156_950, 136_620, 132_050]
    rr = a.industry_ratios()
    assert [r(rr["513200"][q]) for q in a.Q] == [1.27, 1.07, 0.99, 1.00, 1.12] and r(rr["519200"]["p50"]) == 0.76
    assert sum(1 for v in rr.values() for x in v.values() if x > 1) == 18
    assert all(x < 1 for x in rr["519200"].values())


def test_small_runs():
    assert fr.percentile_ratio({"p50": 2}, {"p50": 1}, ("p50",)) == {"p50": 2.0}
    assert fr.card("site reliability engineer").chapter == 20
