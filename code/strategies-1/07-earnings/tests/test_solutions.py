"""Numbers gate: every numerical answer printed in Book 8, chapter 7 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_earnings import announcers, car, moves, run  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_event_books():
    assert [r(run(h, "surprise", False, 0)["sr"]) for h in (5, 20, 60)] == [-3.72, 0.02, 2.03]
    got = [(r(run(h)["sr"]), r(run(h)["sr_gross"]), r(100 * run(h)["ret"], 1), r(run(h)["turnover"], 1))
           for h in (5, 20, 60)]
    assert got == [(-0.77, 1.38, -4.7, 65.2), (1.51, 2.64, 4.6, 17.2), (2.66, 3.31, 5.5, 6.6)]
    assert [r(run(h, "ear")["sr"]) for h in (5, 20, 60)] == [-0.85, 0.85, 2.03]
    early, late = run(60)["sr_early"], run(60)["sr_late"]
    cut = run(60, "surprise", True)
    assert (r(early), r(late), r(cut["sr_early"]), r(cut["sr_late"]), r(cut["sr"])) == \
        (2.18, 3.24, 2.18, 0.75, 1.51)
    assert (r(100 * cut["ret_early"], 1), r(100 * cut["ret_late"], 1), r(100 * run(60)["ret_late"], 1)) == (4.8, 1.4, 6.2)
    assert [r(run(h, "surprise", True)["sr_late"]) for h in (5, 20)] == [-1.19, -0.51]
    assert r(run(20, "surprise", True)["sr_early"]) == 1.48
    assert r(100 * (run(5)["ret"] + 2 * 65.2 * 0.001), 1) == 8.3


def test_event_study_and_moves():
    c = car(5, 60)
    assert [r(100 * c["positive"][i]) for i in (5, 6, 25, 65)] == [6.94, 6.61, 7.01, 7.75]
    assert [r(100 * c["negative"][i]) for i in (5, 6, 25, 65)] == [-6.93, -6.64, -7.31, -8.56]
    m = moves()
    assert (r(m["ratio"]), r(100 * m["event_share"]), r(252 * m["event_share"], 1)) == (3.02, 1.59, 4.0)
    a = announcers()
    assert (r(a["mean_daily_bp"], 1), r(a["t"])) == (1.8, 0.59)


def test_exercises():
    assert r(1.5 * 0.012 * 100, 1) == 1.8 and r(0.012 / 60 * 1e4, 1) == 2.0
    assert r(2 * 65.2 * 0.001 * 100, 1) == 13.0 and r(2 * 6.6 * 0.001 * 100, 1) == 1.3
    assert r(0.05 * 6.94, 2) == 0.35
    assert r((13 / 5) ** 0.5, 2) == 1.61 and r(3.02**2, 0) == 9
