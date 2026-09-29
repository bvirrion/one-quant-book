import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_crisisdrill as cd  # noqa: E402

ACC = [cd.Account("A", 10.0, 10.0), cd.Account("B", 10.0, 10.0), cd.Account("FCM", 5.0, 5.0)]


def sc(**kw):
    return cd.Scenario(tuple([1.0, 1.5, 1.5, 1.5]), tuple([1.0] * 4), "FCM", **kw)


def test_calls_and_horizon():
    r = cd.run(ACC, 8.0, sc(), (), 4)
    assert r["cash"][0] == pytest.approx(8.0) and r["cash"][1] == pytest.approx(-2.0) and r["horizon"] == 1


def test_failure_trap_and_move():
    s = sc(failed="B", fail_hour=0, trapped=0.5, return_hour=2, moved_to="A")
    r = cd.run(ACC, 20.0, s, (), 4)
    assert r["cash"][0] == pytest.approx(10.0)            # A must hold 20 at hour 0: a call of 10
    assert r["cash"][1] == pytest.approx(0.0)             # 30 at 1.5x: a further call of 10
    assert r["cash"][2] == pytest.approx(5.0)             # half of B's 10 comes back


def test_actions_and_greedy():
    menu = [cd.Action("cash", cash=5.0, delay=0, cost=1.0), cd.Action("cut", cut=0.5, delay=0, cost=5.0)]
    chosen, res = cd.greedy(ACC, 8.0, sc(), menu, 4, 4)
    assert [a.name for a in chosen] == ["cash"] and res["horizon"] == 4
    late = cd.Action("late line", cash=100.0, delay=3, deadline=2)
    assert cd.run(ACC, 8.0, sc(), [late], 4)["horizon"] == 1
