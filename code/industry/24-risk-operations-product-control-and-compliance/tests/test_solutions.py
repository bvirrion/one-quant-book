"""Numbers gate: every numerical answer printed in Book 17, chapter 24 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_control as a  # noqa: E402

fr = a.fr


def r(x, d=3):
    return round(float(x), d)


def test_ratios():
    g = a.ratios()
    b = g[(2025, "bank", "all")]
    assert (b["n_control"], b["emp_control"], b["n_front"], b["emp_front"]) == (380, 5, 883, 9)
    assert (b["median_control"], b["median_front"], b["diff"], b["diff_lo"], b["diff_hi"]) == (
        136_776, 160_000, -23_224, -31_100, -15_195)
    assert (r(b["ratio"]), r(b["ratio_lo"]), r(b["ratio_hi"])) == (0.855, 0.807, 0.903)
    assert [r(g[(2025, "bank", lv)]["ratio"], 2) for lv in a.LEVELS] == [0.68, 0.79, 0.85, 0.83]
    t = g[(2025, "trading firms", "all")]
    assert (t["n_control"], t["emp_control"], t["median_control"]) == (17, 7, 193_003)
    assert (r(t["ratio"]), r(t["ratio_lo"]), r(t["ratio_hi"])) == (0.965, 0.925, 1.151)
    o = g[(2021, "bank", "all")]
    assert (r(o["ratio"], 2), o["median_control"], o["median_front"]) == (1.01, 131_720, 130_000)
    assert r(100 * (160_000 / 130_000 - 1), 1) == 23.1 and r(100 * (136_776 / 131_720 - 1), 1) == 3.8


def test_mix_and_survey():
    e = a.eba()
    assert e["Independent control functions"][0] == 53 and r(e["Independent control functions"][1], 2) == 0.88
    assert r(e["Investment banking"][1], 2) == 1.23
    m = a.mix()
    assert (r(100 * m["fixed_control"], 1), r(100 * m["fixed_business"], 1), r(m["ratio_of_ratios"], 2)) == (
        53.3, 44.8, 0.71)
    assert r(100 * fr.fixed_share(0.88), 1) == 53.2 and r(e["Independent control functions"][1], 4) == 0.8775
    s = a.survey()
    assert [int(s[k]["p50"]) for k in ("13-2054", "13-2011", "13-1041", "43-4011")] == [133_070, 105_160, 100_160,
                                                                                         70_070]


def test_small_runs():
    assert fr.mix_gap(1.0, 1.0)["ratio_of_ratios"] == 1.0
    assert fr.card("product controller").chapter == 24
