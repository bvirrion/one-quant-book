"""Numbers gate: every numerical answer printed in Book 17, chapter 19 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_quantdev as a  # noqa: E402

fr = a.fr


def r(x, d=1):
    return round(float(x), d)


def test_mix_and_cells():
    mix, tot = a.soc_mix()
    q = mix["quant developer"]
    assert (tot["quant developer"], q["13-2099.01"], q["15-1252"], q["other"]) == (169, 122, 25, 22)
    assert [r(100 * q[k] / 169) for k in ("13-2099.01", "15-1252", "other")] == [72.2, 14.8, 13.0]
    qd = a.quantdev_cells()
    assert qd[(2025, "systematic fund")] == (12, 3, False) and qd[(2025, "bank")] == (137, 1, True)
    assert sum(n for (fy, _), (n, _, _) in qd.items() if fy == 2025) == 169
    with open(a.DATA / "lca_ranges.csv") as f:
        row = [x for x in f if x.startswith("2025,systematic fund,quant developer,all")][0].split(",")
    assert (row[7], row[9], row[11]) == ("195500", "235000", "272500")
    c = a.soc_cells()
    assert (c[("15-1252", "all")]["n"], c[("15-1252", "all")]["p50"]) == (5531, 155_000)
    assert (c[("13-2099.01", "all")]["n"], c[("13-2099.01", "all")]["p50"]) == (1294, 150_000)
    assert [c[("15-1252", lv)]["p50"] for lv in a.LEVELS] == [105_000, 139_300, 164_000, 167_300]
    assert [c[("13-2099.01", lv)]["p50"] for lv in a.LEVELS] == [112_500, 140_000, 175_000, 194_392]
    assert a.soc_cells(2025, "bank")[("15-1252", "all")]["n"] == 4790
    assert a.soc_cells(2025, "bank")[("15-1252", "all")]["employers"] == 8


def test_gaps():
    g = a.gaps()
    x = g[(2025, "all")]
    assert (x["diff"], x["diff_lo"], x["diff_hi"]) == (5000, -372, 5688)
    assert (g[(2025, "III")]["diff"], g[(2025, "III")]["diff_lo"], g[(2025, "III")]["diff_hi"]) == (-11000, -19038, -6600)
    assert (g[(2025, "IV")]["diff"], g[(2025, "IV")]["diff_lo"], g[(2025, "IV")]["diff_hi"]) == (-27092, -37500, -19900)
    m = a.level_mix()
    assert [r(100 * v) for v in m["13-2099.01"]] == [7.8, 51.1, 26.7, 14.4] and r(100 * m["15-1252"][3]) == 50.4
    assert round(a.reweighted_gap()) == -7789
    assert sum(1 for v in g.values() if v["diff_lo"] > 0 or v["diff_hi"] < 0) == 5
    assert all(v["diff"] < 0 for (fy, lv), v in g.items() if fy == 2025 and lv != "all")


def test_titles_and_survey():
    t = {x[0]: x[1:] for x in a.titles()}
    assert all(t[k] == ("QUANTITATIVE DEVELOPER", s) for k, s in (("Sr. Quant Developer - Equities", "senior"),
                                                                 ("VP, Quant Dev", "vice president"),
                                                                 ("Quant Dev L3", "")))
    assert fr.normalise_title("Sr. Quant Dev (Rates), NY") == ("QUANTITATIVE DEVELOPER", "senior")
    s = a.survey()
    assert [int(s["523000"][k]) for k in ("employment", "p10", "p50", "p90")] == [34_940, 104_600, 163_290, 245_380]
    assert (int(s["5220A1"]["p50"]), int(s["513200"]["p50"]), int(s["513200"]["employment"])) == (136_620, 164_550,
                                                                                                 173_080)
    assert round(163_290 / 136_620, 3) == 1.195


def test_small_runs():
    rng = np.random.default_rng(0)
    g = fr.median_gap(rng.normal(10, 1, 30), rng.normal(8, 1, 30), rng, n_boot=200)
    assert g["diff_lo"] < 2 < g["diff_hi"] or abs(g["diff"] - 2) < 1
    assert fr.card("research engineer").chapter == 19
