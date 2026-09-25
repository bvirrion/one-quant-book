"""Numbers gate: every numerical answer printed in Book 8, chapter 4 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_pairs import calibration, discoveries, run, takeover, true_selected  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def row(share, m):
    x = run(share, m)
    return (r(x["sr_gross"]), r(x["sr_net"]), r(100 * x["ret_net"], 1), r(x["opened"]), r(100 * x["never"], 0))


def test_books():
    assert row(0.1, "distance") == (5.34, 5.05, 12.2, 2.11, 51)
    assert row(0.1, "copula") == (4.39, 3.89, 11.6, 4.28, 89)
    assert row(0.1, "two-step") == (1.16, 1.03, 5.9, 2.24, 75)
    assert row(0.1, "eg") == (-0.09, -0.17, -1.4, 2.02, 81)
    assert row(0.1, "twin") == (-0.45, -0.49, -2.6, 0.87, 61)
    assert [r(run(0.0, m)["sr_net"]) for m in ("distance", "copula", "two-step", "eg", "twin")] == \
        [-0.43, -0.5, -0.11, -0.47, -0.35]
    assert [r(100 * run(0.0, m)["never"], 0) for m in ("distance", "eg")] == [84, 89]
    assert [true_selected(m) for m in ("distance", "eg", "two-step")] == [311, 40, 113]


def test_discoveries():
    t = {k: sum(x[k] for x in discoveries(0.1)) for k in discoveries(0.1)[0] if k != "t0"}
    assert (t["tested"], t["raw"], t["fdr"], t["true_fdr"], t["true_pairs"], t["true_raw"]) == \
        (745465, 58024, 1139, 32, 626, 530)
    assert (r(100 * t["raw"] / t["tested"], 1), r(100 * (1 - t["true_fdr"] / t["fdr"]), 1),
            r(100 * t["true_raw"] / t["true_pairs"], 1)) == (7.8, 97.2, 84.7)
    assert (r(100 * t["again"] / t["followed"], 1), r(100 * t["true_again"] / t["true_followed"], 1),
            r(100 * (t["again"] - t["true_again"]) / (t["followed"] - t["true_followed"]), 1)) == (7.9, 84.6, 7.2)
    assert (t["again"], t["true_again"], r(100 * t["true_again"] / t["again"], 1), r(100 * t["true_raw"] / t["raw"], 2)) == \
        (4020, 401, 10.0, 0.91)
    assert r(t["true_again"] / t["again"] / (t["true_raw"] / t["raw"]), 0) == 11
    u = {k: sum(x[k] for x in discoveries(0.0)) for k in ("tested", "raw", "fdr")}
    assert (u["tested"], u["raw"], u["fdr"], r(100 * u["raw"] / u["tested"], 1)) == (742028, 55066, 959, 7.4)


def test_calibration_and_example():
    c = calibration()
    assert [r(100 * c[x], 2) for x in (0.001, 0.01, 0.05, 0.1)] == [0.32, 1.97, 7.42, 13.16]
    e = takeover()
    assert (e["day"], e["reason"], e["twins"], e["opened"], e["side"]) == (111, "merger", True, 2, 1)
    assert (r(100 * e["pnl"][-1], 1), r(100 * e["spread"].max(), 1), r(100 * e["sd"], 1)) == (-24.6, 35.1, 2.4)


def test_exercises():
    assert 45 * 44 // 2 * 10 == 9900 and r(9900 * 0.05, 0) == 495
    assert r(0.05 * 20 / 1000, 3) == 0.001
    assert r(4 * 0.0005 * 1e4, 0) == 20
    assert r(2 * 0.024 * 100, 1) == 4.8
