"""Numbers gate: every numerical answer printed in Book 16, chapter 20 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_buildbuy as m  # noqa: E402

bb = m.bb


def r(x, d=2):
    return round(float(x), d)


def test_paths():
    b, y = m.paths()
    assert [r(x, 3) for x in b] == [3.185, 3.185, 1.565, 1.565, 1.565, 1.565, 1.565]
    assert [r(x, 3) for x in y] == [3.565, 1.715, 1.778, 1.844, 1.914, 1.987, 2.063]
    assert r(sum(b), 1) == 14.2 and r(sum(y), 1) == 14.9 and r(0.35 * 1.3, 3) == 0.455


def test_summary():
    s = m.summary()
    assert (r(s["build"]), r(s["buy"]), r(s["breakeven_wage"], 3), s["breakeven_horizon"]) == (11.04, 11.3, 0.363, 7)
    assert (r(s["buy_with_price_risk"]), r(s["buy_with_switch"]), r(s["switch_value"])) == (13.46, 12.9, 0.56)
    h = m.by_horizon()
    assert [(x[0], r(x[1]), r(x[2])) for x in h if x[0] in (1, 3, 5, 6, 7, 10)] == [
        (1, 2.95, 3.3), (3, 6.92, 6.18), (5, 9.14, 8.84), (6, 10.12, 10.09), (7, 11.04, 11.3), (10, 13.39, 14.64)]


def test_tornado():
    t = m.tornado()
    assert [k for k, _, _ in t][:4] == ["licence", "wage", "dev_engineers", "maint_engineers"]
    assert [(r(lo), r(hi)) for _, lo, hi in t[:2]] == [(1.17, -1.69), (-1.69, 1.17)] and r(m.diff(m.BASE)) == -0.26


def test_small_runs():
    stay, flex, opt = bb.switch_value(m.Y, 3, 0.08, 1.3, 0.0, 2.0)
    assert abs(opt) < 1e-12 and abs(stay - bb.npc(bb.buy_costs(m.Y, 3), 0.08)) < 1e-12


def test_exercises():
    stay, flex, opt = bb.switch_value(m.Y, 7, 0.08, 1.3, 0.5, 2.0)
    assert (r(stay), r(flex), r(opt)) == (15.28, 13.79, 1.5)
    assert r(1.2 * 1.05 ** 6) == 1.61 and r(m.summary()["buy_with_price_risk"] - m.summary()["build"]) == 2.42


def test_policy():
    pol = bb.switch_policy(m.Y, 7, 0.08, 1.3, 0.3, 2.0)
    assert [k for t, k in pol if t == 3] == [2] and min(k for t, k in pol if t == 7) == 4
    assert all(k >= 2 for _, k in pol) and r(1.3 ** 2, 2) == 1.69
