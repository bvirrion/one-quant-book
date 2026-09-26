"""Numbers gate: every numerical answer printed in Book 10, chapter 27 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_agents import FACTS, ablation, calibration, distance, maker_study, sign_curves, target  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


def test_calibration_named_result():
    t, c = target(), calibration()
    assert c["best"] == (1.2, 2.5, 0.05) and c["start"] == (0.9, 0.0, 0.0)
    assert (r(c["distance"]), r(c["distance_start"]), r(c["distance_fresh"]), r(c["floor"])) == (10.1, 27.9, 5.4, 1.7)
    assert (r(c["facts"]["kurtosis"], 2), r(c["fresh"]["kurtosis"], 2)) == (3.11, 1.90)
    z = {k: (c["fresh"][k] - t["mean"][k]) / t["sd"][k] for k in FACTS}
    worst = sorted(FACTS, key=lambda k: -abs(z[k]))[:3]
    assert set(worst) == {"absret_acf", "depth", "sign_acf1"} and z["absret_acf"] < 0 and z["depth"] < 0 < z["sign_acf1"]
    # exercise 1
    assert (r(t["mean"]["sign_acf1"], 3), r(t["sd"]["sign_acf1"], 3), r(c["fresh"]["sign_acf1"], 3)) == (0.158, 0.046, 0.212)
    assert r((0.212 - 0.158) / 0.046, 2) == 1.17 and r(1.17**2) == 1.4 and r(z["sign_acf1"] ** 2 / c["distance_fresh"], 2) == 0.26
    # exercise 3 and 4
    assert r(7 * (1 / 6 + 1 / 8)) == 2.0 and r(c["distance_fresh"] / 2.0) == 2.7 and r(7 * (1 / 3 + 1 / 8)) == 3.2
    # the surface: tail 2.5 with chartists is the valley
    s = c["surface"]
    assert min(s, key=s.get) == (1.2, 2.5, 0.05) and r(s[(1.2, 2.5, 0.1)]) == 10.4


def test_exercise_7_five_facts():
    t, c = target(), calibration()
    five = FACTS[:5]
    rows = sorted((distance({k: m[k] for k in five}, {k: t["mean"][k] for k in five}, t["sd"]), p, m)
                  for _, p, m in c["all"])
    (d1, p1, m1), (d2, p2, _) = rows[0], rows[1]
    assert (p1, r(d1), p2, r(d2)) == ((1.5, 2.5, 0.1), 5.1, (1.2, 2.5, 0.05), 7.7)
    assert r(m1["depth"], 0) == 9 and r(m1["spread"], 2) == 1.08 and (m1["spread"] - t["mean"]["spread"]) / t["sd"]["spread"] > 2
    assert r(t["mean"]["depth"], 0) == 24 and r(t["mean"]["spread"], 2) == 1.04


def test_ablation_table():
    a = ablation()
    want = {"runs": [(1.32, 0.79), (0.02, 0.29), (-0.63, 1.12), (-2.77, 0.15), (-0.35, 0.25), (-0.38, 0.19), (0.10, 0.06)],
            "chartists": [(1.11, 0.55), (-0.10, 0.20), (-0.72, 0.67), (0.02, 0.10), (-0.18, 0.27), (-0.29, 0.11),
                          (0.09, 0.02)],
            "fundamentalists": [(8.55, 2.65), (-0.47, 0.25), (-0.73, 0.88), (0.87, 0.14), (-2.42, 0.40), (-1.29, 0.15),
                                (0.96, 0.05)],
            "maker": [(-0.79, 0.29), (-1.77, 0.25), (0.31, 0.57), (-0.69, 0.10), (-1.00, 0.19), (9.44, 0.37),
                      (-0.75, 0.04)]}
    for d, row in want.items():
        assert [(r(a[d]["z"][k], 2), r(a[d]["se"][k], 2)) for k in FACTS] == row, d
    assert [a[d]["carried"] for d in want] == ["sign_acf1", "kurtosis", "kurtosis", "spread"]
    assert r(a["maker"]["facts"]["spread"] - a["full"]["spread"], 2) == 0.15
    assert a["noise"]["facts"]["sign_acf1"] > 0.95


def test_sign_curves_and_maker():
    s = sign_curves()
    assert (r(s["slope"], 2), s["implied"]) == (-1.15, -1.5)
    assert abs(s["excess"][5]) < 0.005 and all(0.065 < x < 0.095 for x in s["none"][:8])
    m = maker_study()
    got = [(r(m[k]["inventory_rms"]), r(m[k]["pnl"], 0), r(m[k]["pnl_sd"], 0), r(m[k]["spread"], 3)) for k in (0.0, 0.1, 0.3)]
    assert got == [(14.5, -116, 203, 1.031), (4.2, 448, 98, 1.023), (1.6, 545, 67, 1.024)]
    assert max(abs(x) for x in m[0.0]["path"][1]) >= 20
