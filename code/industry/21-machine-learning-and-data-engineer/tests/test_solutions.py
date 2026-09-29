"""Numbers gate: every numerical answer printed in Book 17, chapter 21 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_mldata as a  # noqa: E402

fr = a.fr


def r(x, d=1):
    return round(float(x), d)


def test_counts_and_growth():
    c = a.counts()
    assert [(c[(2021, f)], c[(2025, f)]) for f in a.FAMILIES] == [(136, 1051), (2618, 5727), (22, 169), (197, 421),
                                                                  (1287, 1297), (147, 129)]
    tot, sh = a.shares()
    assert tot == {2021: 4422, 2025: 8808} and (r(100 * sh[2021]), r(100 * sh[2025])) == (3.1, 11.9)
    assert a.by_kind()[(2025, "bank")] == 920
    t = a.trends()
    m, s, q = t["ml and data"], t["software engineer"], t["quant researcher"]
    assert (r(100 * m["annual"]), r(100 * m["lo"]), r(100 * m["hi"])) == (66.7, 59.4, 74.3)
    assert (r(100 * s["annual"]), r(100 * s["lo"]), r(100 * s["hi"])) == (21.6, 20.2, 23.0)
    assert (r(100 * q["annual"]), r(100 * q["lo"]), r(100 * q["hi"])) == (0.2, -1.7, 2.1)
    assert t["trader"]["annual"] < 0 and (round(m["rate"], 3), round(m["se"], 3)) == (0.511, 0.023)
    assert round(s["se"], 4) == 0.0059 and r(1051 / 136, 2) == 7.73
    lo, hi = fr.poisson_interval(1051)
    assert (round(lo), round(hi)) == (988, 1117)


def test_gap_and_survey():
    g = a.gaps()
    assert (g["all"]["median_ds"], g["all"]["median_dev"]) == (138_000, 155_000)
    assert (g["all"]["diff"], g["all"]["diff_lo"], g["all"]["diff_hi"]) == (-17_000, -20_000, -15_000)
    assert [g[lv]["diff"] for lv in a.LEVELS] == [-20_500, -18_300, -19_000, 2_220]
    with open(a.DATA / "lca_ranges.csv") as f:
        rows = [x.split(",") for x in f if x.startswith("2025,") and ",ml and data,all," in x]
    med = {x[1]: (x[9], x[4]) for x in rows}
    assert med["market maker"] == ("175000", "11") and med["multi-manager platform"] == ("193000", "12")
    assert med["systematic fund"] == ("192912", "10")
    s = a.survey()
    assert [(int(s[k]["employment"]), int(s[k]["p50"])) for k in ("52", "51", "54")] == [
        (46_730, 124_770), (32_410, 141_440), (69_730, 126_730)]
    assert [int(s[k]["employment"]) for k in ("5220A1", "524100", "523000", "513200")] == [12_450, 15_090, 7_210,
                                                                                         10_950]
    assert [int(s[k]["p50"]) for k in ("5220A1", "524100", "523000", "513200")] == [130_300, 107_680, 134_510,
                                                                                  156_220]


def test_exercises():
    g = math.log(1051 / 136) / 4
    se = math.sqrt(1 / 136 + 1 / 1051) / 4 * math.sqrt(10)
    assert round(se, 3) == 0.072 and (r(100 * (math.exp(g - 1.96 * se) - 1)), r(100 * (math.exp(g + 1.96 * se) - 1))) == (
        44.8, 92.0)


def test_small_runs():
    assert fr.filing_trend([0, 1], [10, 20])["rate"] > 0
    assert fr.card("data scientist").chapter == 21
