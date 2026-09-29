"""Numbers gate: every numerical answer printed in Book 17, chapter 1 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_map as m  # noqa: E402

im = m.im


def r(x, d=1):
    return round(float(x), d)


def test_sample_composition():
    c = m.counts()
    assert sum(v[0] for v in c.values()) == 21
    assert c["market maker"][0] == 11 and c["systematic fund"][0] == 4 and c["multi-manager platform"][0] == 2
    assert c["bank"][0] == 2 and c["asset manager"][0] == 1 and c["exchange"][0] == 1
    assert sum(v[1] for v in c.values()) == 5  # issuers carry SIC codes


def test_accuracy_table_and_figure():
    a = m.accuracy()
    assert a["SIC code"] == {"coarse": (3, 21), "fine": (3, 21)}
    assert a["forms filed"] == {"coarse": (15, 21), "fine": (13, 21)}
    assert a["forms, then SIC"] == {"coarse": (18, 21), "fine": (16, 21)}
    assert [r(100 * a[k]["coarse"][0] / 21, 0) for k in a] == [14, 71, 86]
    assert len(m.misses()) == 3 and "Tower Research Capital LLC" in m.misses()


def test_sic_unknowns():
    es = m.sample()
    assert sum(im.by_sic(e) == im.UNKNOWN for e in es) == 16


def test_exercise_7_new_rule():
    def rule(e):
        if "issuer" in e.families and e.sic == "6211" and "13F" in e.families:
            return "asset manager"
        return im.combined(e)
    assert im.score(m.sample(), rule, "coarse") == (19, 21)
    wrong = [e.name for e in m.sample() if im._level(rule(e), "coarse") != im._level(e.truth, "coarse")]
    assert wrong == ["Tower Research Capital LLC", "GOLDMAN SACHS GROUP INC"]


def test_finra():
    f = m.finra_2024()
    assert f["bd"] == 3249 and f["ia_only"] == 32090 and f["prop"] == 103
    assert r(100 * f["small"] / f["bd"]) == 89.0 and r(100 * 93 / f["prop"]) == 90.3
    y = m.finra()
    bd15 = y[0]["bd_only"] + y[0]["dual"]
    assert bd15 == 3943 and r(100 * (3249 - bd15) / bd15) == -17.6
    assert r(100 * (32090 - y[0]["ia_only"]) / y[0]["ia_only"]) == 11.8
    assert r(bd15 / 1000, 2) == 3.94 and r(y[0]["ia_only"] / 1000, 1) == 28.7 and r(32090 / 1000, 1) == 32.1


def test_estimate_iq4():
    lo = 80 * 20 + 20 * 100 + 10 * 500
    hi = 80 * 100 + 20 * 500 + 10 * 3000
    assert (lo, hi) == (8600, 48000)
