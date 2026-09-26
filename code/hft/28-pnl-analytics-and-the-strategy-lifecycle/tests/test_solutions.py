"""Numbers gate: every numerical answer printed in Book 11, chapter 28 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_attrib as h  # noqa: E402


def r(x, d=-2):
    return round(float(x), d)


def test_detection_and_experiment():
    d = h.detect()
    assert (d["day"], d["day_ratio"], round(100 * d["comp_share"], 1), round(100 * d["comp_kappa"], 1)) == (176, 176, 29.9, 14.9)
    e = h.exp()
    assert (r(e["effect"], -1), r(e["se"], -1), r(e["cuped"], -1), r(e["cuped_se"], -1)) == (-2670, 1070, -2550, 1070)
    assert (e["n_treated"], e["n"], round(e["share_mult"], 6), round(e["adverse_add"], 6)) == (33, 70, 1.1, 0.1)


def test_month9_and_retirement():
    m = h.month9()
    t, e = m["truth"], m["estimate"]
    assert [r(t[k]) for k in ("spread", "volume", "competition", "parameter", "residual", "realised")] == [
        -51500, 48000, -57400, -8100, 23400, -45600]
    assert [r(e[k]) for k in ("competition", "parameter", "residual")] == [-53500, -8100, 19600]
    for s, exp in ((2, (6400, 2600, -53400, -57300)), (3, (-3600, -7600, -55400, -59400))):
        mm = h.month9(s)
        assert (r(mm["truth"]["residual"]), r(mm["estimate"]["residual"]), r(mm["estimate"]["competition"]),
                r(mm["truth"]["competition"])) == exp
    d = h.daily()
    assert (r(d[:147].mean()), r(d[189:].mean())) == (16600, 12200)
    assert (h.retirement(cost_per_day=12000.0), h.retirement(cost_per_day=13000.0), h.retirement(cost_per_day=10000.0)) == (239, 221, -1)


def test_exercises():
    assert round(15e6 * 0.12 * (0.8 - 0.35) / 100) == 8100 and round(15e6 * 0.084 * (0.68 - 0.35) / 100) == 4158
    assert round(15e6 * 0.132 * (0.80 - 0.45) / 100) == 6930
    assert round(2 * (1.96 + 0.84) ** 2 * 4500**2 / 2000**2) == 79
