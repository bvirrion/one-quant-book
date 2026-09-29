"""Numbers gate: every numerical answer printed in Book 17, chapter 14 (text and solutions)."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_paylevels as a  # noqa: E402

pd = a.pd
RG = a.ranges()


def med(kind, role="all", level="all", fy=2025):
    return RG[(fy, kind, role, level)]["p50"]


def test_counts_and_rules():
    c = a.counts()
    want = {"bank": (7298, 9), "market maker": (367, 10), "systematic fund": (210, 7),
            "multi-manager platform": (102, 3), "exchange": (462, 4), "asset manager": (369, 1)}
    assert {k: c[(2025, k)] for k in want} == want
    w21 = {"bank": (3539, 9), "market maker": (259, 10), "systematic fund": (143, 5),
           "multi-manager platform": (53, 3), "exchange": (228, 4), "asset manager": (200, 1)}
    assert {k: c[(2021, k)] for k in w21} == w21
    kinds = [r.kind for r in pd.load_rules(a.DATA / "lca_employers.csv")]
    assert [kinds.count(k) for k in ("market maker", "systematic fund", "multi-manager platform", "bank",
                                     "asset manager", "exchange")] == [12, 7, 4, 9, 1, 4]
    assert all(v["suppressed"] for k, v in RG.items() if k[1] == "asset manager")
    assert all(v["suppressed"] for v in RG.values() if v["n"] < 10 or v["employers"] < 3)


def test_median_table():
    kinds = ("systematic fund", "multi-manager platform", "market maker", "bank", "exchange")
    assert [round(med(k) / 100) / 10 for k in kinds] == [215.0, 190.5, 175.0, 154.3, 130.8]
    assert [round(med(k, "quant researcher") / 100) / 10 for k in kinds] == [220.0, 190.0, 175.0, 158.1, 107.1]
    assert [round(med(k, "software engineer") / 100) / 10 for k in kinds] == [205.5, 190.0, 175.0, 155.7, 140.4]
    assert med("market maker", "trader") == 195_000 and med("bank", "trader") == 235_000
    for k in ("systematic fund", "multi-manager platform", "exchange"):
        assert (2025, k, "trader", "all") not in RG or RG[(2025, k, "trader", "all")]["suppressed"]
    assert med("systematic fund") - med("exchange") == 84_200
    assert round(100 * (med("systematic fund") / med("exchange") - 1), 1) == 64.4
    q = RG[(2025, "market maker", "quant researcher", "all")]
    assert round(q["p25"], -2) == 132_400 and q["p75"] == 237_500


def test_growth_and_levels():
    g = {k: round(100 * a.growth(k, "all"), 1) for k in a.KINDS}
    assert g == {"systematic fund": 22.9, "multi-manager platform": 18.7, "market maker": 16.7, "bank": 22.9,
                 "exchange": 7.9}
    assert round(100 * (135.8312 / 114.325 - 1), 1) == 18.8
    assert med("bank", level="I") == 100_000 and med("bank", level="IV") == 169_900
    assert med("market maker", level="I") == 84_800 and med("market maker", level="II") == 180_000
    assert med("market maker", level="III") == 185_000 and med("market maker", level="IV") == 185_000
    assert med("market maker", "quant researcher", "III") < med("market maker", "quant researcher", "II")
    assert RG[(2025, "market maker", "quant researcher", "III")]["n"] == 26
    assert RG[(2025, "market maker", "quant researcher", "II")]["n"] == 81
    assert round(150_000 * 135.83 / 114.33) == 178_208
    assert round(100 * (1 - 175_000 / (150_000 * 135.83 / 114.33)), 1) == 1.8


def test_oews():
    o = a.oews()
    s = o[("523000", "15-1252")]
    assert (int(s["p50"]), int(s["p25"]), int(s["p75"])) == (163290, 132650, 203840)
    assert int(o[("5220A1", "15-1252")]["p50"]) == 136620 and int(o[("523000", "13-2051")]["p50"]) == 124370


def test_ratios():
    imp = a.implied_ratios()
    mm, sf, bk = imp["market maker"], imp["systematic fund"], imp["bank"]
    assert (round(mm["lo"] / 1e6, 2), round(mm["hi"] / 1e6, 2)) == (0.78, 2.11)
    assert (round(mm["r_lo"], 1), round(mm["r_hi"], 1)) == (4.4, 12.0)
    assert round(sf["lo"] / 1e6, 2) == 4.11 and round(sf["r_lo"], 1) == 19.1
    assert (round(bk["lo"], -3), round(bk["hi"], -3)) == (342_000, 399_000)
    assert (round(bk["r_lo"], 1), round(bk["r_hi"], 1)) == (2.2, 2.6)
    m = a.median_ratios()
    assert round(m["Intercontinental Exchange"]["mean"]) == 152_834 and round(m["Nasdaq"]["mean"]) == 146_142
    assert [round(m[f]["ratio"], 2) for f in ("Intercontinental Exchange", "Nasdaq", "Morgan Stanley")] == [
        1.35, 1.43, 2.58]
    assert m["Morgan Stanley"]["mean"] == 352_000


def test_eba_tail():
    e = a.eba()
    ib, oa = e[("credit institutions", "Investment banking")], e[("investment firms", "Dealing on own account")]
    assert int(float(ib["high_earners"])) == 904 and round(float(ib["variable_to_fixed"]), 2) == 1.23
    assert int(float(oa["high_earners"])) == 97 and round(float(oa["variable_to_fixed"]), 2) == 8.14
    assert round(float(oa["avg_total_eur"]) / 1e6, 2) == 2.09
    assert round(float(oa["avg_total_eur"]) * a.eur_usd(2025) / 1e6, 2) == 2.37
    t = e[("credit institutions", "Total")]
    assert int(float(t["high_earners"])) == 2266 and round(float(t["variable_to_fixed"]), 2) == 0.99
    assert int(float(e[("investment firms", "Total")]["high_earners"])) == 288 and 2266 + 288 == 2554


def test_exercise_arithmetic_and_suppressed():
    assert pd.annualise(95, "Hour") == 197_600 and pd.annualise(16_000, "Month") == 192_000
    with open(a.DATA / "lca_ranges.csv") as f:
        sup = [r for r in csv.DictReader(f) if r["fy"] == "2025" and r["kind"] == "market maker"
               and r["suppressed"] == "1"]
    assert len(sup) == 14 and all(int(r["n"]) < 10 for r in sup)


def test_small_runs():
    ev = a.evidence()
    assert len(ev) == 3 and all(e.lo <= e.hi for e in ev)
