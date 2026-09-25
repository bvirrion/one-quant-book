"""Numbers gate: every numerical answer printed in Book 9, chapter 11 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_basis import parts, real, table  # noqa: E402


def pct(x, d=1):
    return round(100 * float(x), d)


def test_books():
    got = {L: (pct(v["before"]), pct(v["trough"]), pct(v["after"]), v["forced"], pct(v["five_years"]),
               round(v["face_after"], 1)) for L, v in table().items()}
    assert got == {10: (2.1, -6.1, -0.2, 0, 1.9, 10.4), 20: (4.1, -10.8, -1.9, 10, 3.5, 16.5),
                   30: (6.2, -13.2, -4.5, 10, 4.8, 16.8), 50: (10.3, -17.8, -9.6, 66, 7.1, 17.5)}
    assert {k: pct(v, 2) for k, v in parts(50).items()} == {"carry": 0.8, "marks": -6.56, "funding": -0.55, "costs": -3.33}
    assert {k: pct(v, 2) for k, v in parts(10).items()} == {"carry": 0.56, "marks": -0.39, "funding": -0.38, "costs": 0.0}


def test_real():
    x = real()
    assert (x["first"], x["last"], x["weeks"], round(float(x["min"])), x["min_at"], round(float(x["2020-02-18"])),
            round(float(x["2020-03-17"])), round(float(x["2017-12-26"])), round(float(x["last_value"])),
            round(float(x["mean_2010_2014"]))) == ("2010-07-20", "2026-09-15", "844", -1184, "2024-11-12", -475, -376,
                                                   -116, -787, 34)


def test_exercises():
    assert (round(1 / (0.01 + 0.01)), round(1 / (0.03 + 0.03), 1), round(50 * 0.006 * 100, 1)) == (50, 16.7, 30.0)
    assert round(0.002 * 50 * 100, 1) == 10.0 and round((659 - 554) / 659 * 100, 1) == 15.9


def test_cap_and_same_terms():
    from s2_basis import forced_before_stress, same_terms
    f = forced_before_stress()
    assert (f["cuts_before"], round(f["face_before"], 1), round(f["face_after"], 1)) == (25, 60.7, 17.5)
    assert forced_before_stress(20)["cuts_before"] == 0
    s = same_terms()
    assert (s["forced"], pct(s["trough"]), pct(s["after"])) == (66, -27.7, -6.2)
