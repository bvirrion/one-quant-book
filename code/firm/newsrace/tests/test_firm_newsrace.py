import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_newsrace as nr  # noqa: E402


def test_race_by_hand():
    # a 4-tick move: levels 1, 2 and 3 are worth 3, 2 and 1 ticks a lot
    got, taken = nr.race(4, [10, 10, 10, 10], [(1.0, 15), (2.0, 100), (50.0, 100)], stale_ms=20.0)
    assert list(taken[:3]) == [10, 10, 10] and taken[3] == 0
    assert got[0] == 10 * 3 + 5 * 2 and got[1] == 5 * 2 + 10 * 1 and got[2] == 0      # the 50-ms tier is too late
    assert nr.race(1, [10], [(1.0, 10)], 20.0)[0][0] == 0


def test_mm_loss_back_of_queue():
    # others have 10 lots ahead at each level; a tier takes 15 at level 1: 5 of ours at 3 ticks
    loss = nr.mm_loss(4, [20, 0, 0, 0], [10, 10, 10, 10], [(1.0, 15)], 20.0)
    assert loss == 5 * 3
    assert nr.mm_loss(-4, [20, 0, 0, 0], [10, 10, 10, 10], [(1.0, 15)], 20.0) == 15


def test_reentry_and_simulation():
    early, later = nr.reentry(0.0), nr.reentry(5.0)
    assert later > early                                   # the first seconds are toxic
    assert nr.reentry(100.0) < nr.reentry(20.0)
    r = nr.simulate(n=2000, seed=3)
    assert math.isclose(sum(r["share"]), 1.0) and r["share"][0] > 0.5 and r["share"][-1] == 0.0
    assert r["mm_loss_per_release"] > 0 and r["best_reentry"] in (2, 5, 10)
    assert math.isclose(nr.misparse(0.1, 2.0, 10.0), 0.9 * 2.0 - 1.0)
