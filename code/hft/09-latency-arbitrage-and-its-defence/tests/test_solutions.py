"""Numbers gate: every numerical answer printed in Book 11, chapter 9 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_latency as h  # noqa: E402

lr = h.lr


def r(x, d=3):
    return round(float(x), d)


def test_designs():
    d = h.designs()
    got = [(r(v["p_sniped"]), r(v["tax"])) for v in d.values()]
    assert got == [(0.899, 0.449), (0.899, 0.449), (0.0, 0.0), (0.211, 0.106), (0.021, 0.011)]
    c = d["continuous {}"]
    assert r(c["first_loser_gap"], 1) == 7.3 and r(c["tax"] / 0.5, 2) == 0.9
    assert r(d["batch {'tau': 1000.0}"]["tax"] / 0.5, 3) == 0.021


def test_by_latency():
    b = h.by_lp_latency()
    assert [round(100 * b[m]["continuous"]) for m in (20.0, 40.0)] == [12, 75] and r(100 * b[100.0]["continuous"], 1) == 99.9
    kw = h.BASE | {"lp_median": 70.0}
    got = [r(lr.race("asymmetric", **kw, d=d, seed=12)["p_sniped"], 4) for d in (50.0, 110.0, 120.0)]
    assert got == [0.3142, 0.01, 0.0052]


def test_defence():
    d = h.defence()
    got = [(round(v["shares"]), r(100 * v["informed"], 1), r(v["markout"])) for v in d.values()]
    assert got == [(7550, 28.8, 0.174), (5225, 13.4, 0.402), (5875, 18.7, 0.374), (6750, 20.0, 0.33),
                   (7425, 24.6, 0.192), (7175, 29.6, 0.099)]
    assert round(100 * (1 - 5225 / 7550)) == 31 and r((28.8 + 13.4) / 2, 1) == 21.1


def test_exercises():
    assert r(537 / 510, 2) == 1.05 and 60 - 45 == 15
