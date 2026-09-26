"""Numbers gate: every numerical answer printed in Book 10, chapter 18 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_sor import partial_study, passive_study, race, sweep_study, trial  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


def test_race_and_single_sweeps():
    assert race() == [("A", 50, None, 360), ("B", 120, 100, 360), ("C", 200, 150, 360), ("D", 280, 200, 360),
                      ("E", 360, 250, 360)]
    sp, sy = trial(False, 0.0, 1), trial(True, 0.0, 1)
    assert (sp["first"], r(100 * sp["ratio"]), r(sp["cost"], 2)) == (1300, 52.0, 0.73)
    assert sp["by_venue"] == {"A": 500, "B": 200, "C": 200, "D": 200, "E": 200}
    assert (sy["first"], r(100 * sy["ratio"]), r(sy["cost"], 2)) == (2500, 100.0, 0.18)
    assert r((270 + 1200 + 360) / 2500, 2) == 0.73                     # exercise 3
    assert [360 - x for x in (50, 120, 200, 280, 360)] == [310, 240, 160, 80, 0]
    # exercise 2: the provider at C
    hear = 50 + 95
    cancel = {"A": None, "B": hear + 50, "C": hear + 5, "D": hear + 50, "E": hear + 100}
    arrive = {"B": 120, "C": 200, "D": 280, "E": 360}
    found = [v for v in arrive if arrive[v] < cancel[v]]
    assert found == ["B"] and (1000 + 3 * 200) / 2500 == 0.64 and cancel == {"A": None, "B": 195, "C": 150, "D": 195,
                                                                           "E": 245}


def test_jitter_and_ranking():
    s = sweep_study()
    assert [(r(100 * s[(j, False)]["ratio"]), r(100 * s[(j, True)]["ratio"])) for j in (0.0, 0.1, 0.2, 0.4)] == [
        (52.0, 100.0), (53.0, 100.0), (57.6, 99.3), (68.6, 90.3)]
    assert (r(100 * s[(0.2, True)]["full"], 0), r(100 * s[(0.4, True)]["full"], 0)) == (94, 37)
    assert [r(100 * s[("venues", False)][v], 0) for v in "ABCDE"] == [100, 44, 41, 40, 40]
    assert [(v, r(100 * c, 2)) for v, c in s[("rank", False)]] == [("A", 0.30), ("E", 0.56), ("C", 0.63), ("B", 0.69),
                                                                   ("D", 0.72)]
    assert [(v, r(100 * c, 2)) for v, c in s[("rank", True)]] == [("E", -0.10), ("C", 0.10), ("A", 0.30), ("B", 0.30),
                                                                  ("D", 0.30)]
    p = partial_study()
    assert p[(True, False)]["venues"] == ("E", "C") and p[(False, False)]["venues"] == ("A", "B")
    assert (r(100 * p[(True, False)]["ratio"]), r(p[(True, False)]["cost"], 3), r(100 * p[(True, True)]["ratio"])) == (
        99.8, 0.004, 100.0)
    assert (r(100 * p[(False, False)]["ratio"]), r(p[(False, False)]["cost"], 2)) == (71.2, 0.59)
    assert (r(100 * p[(False, True)]["ratio"]), r(p[(False, True)]["cost"], 2)) == (100.0, 0.30)


def test_passive_allocation():
    p = passive_study()
    got = {k: (r(v["cost"], 2), r(100 * v["filled"])) for k, v in p.items()}
    assert got == {"market order": (0.80, 100.0), "highest rebate": (0.77, 22.0), "shortest queue": (0.74, 38.7),
                   "proportional": (0.20, 61.3), "Cont-Kukanov": (0.03, 76.4), "Cont-Kukanov, no dark": (0.06, 69.7)}
    assert [round(x) for x in p["proportional"]["alloc"]] == [0, 266, 171, 255, 140, 169]
    ck = [round(x) for x in p["Cont-Kukanov"]["alloc"]]
    assert ck == [0, 405, 373, 406, 401, 193] and sum(ck) == 1778
    assert [round(x) for x in p["Cont-Kukanov, no dark"]["alloc"]] == [0, 544, 478, 522, 478, 0]
    assert r(p["Cont-Kukanov, no dark"]["cost"] - p["Cont-Kukanov"]["cost"], 2) == 0.03
    low = passive_study(lam_o=0.005)["Cont-Kukanov"]
    assert (round(sum(low["alloc"][1:]), -1), [round(x) for x in low["alloc"][1:]], r(low["cost"], 2)) == (
        4030, [1000, 1000, 751, 1000, 277], -0.24)
