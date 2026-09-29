"""Numbers gate: every numerical answer printed in Book 16, chapter 19 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_tech as m  # noqa: E402

tt = m.tt


def r(x, d=2):
    return round(float(x), d)


def test_virtu():
    v = m.virtu()
    assert [(y, cd) for y, _, cd in v][::6] == [(2019, 209.4), (2025, 249.2)]
    assert (min(x[1] for x in v), max(x[1] for x in v)) == (1517.5, 3632.1)
    assert [r(100 * cd / rev, 1) for _, rev, cd in v] == [13.8, 6.6, 7.5, 9.3, 10.1, 8.2, 6.9]
    assert r(100 * (249.2 / 209.4 - 1), 0) == 19 and r(3632.1 / 1517.5, 1) == 2.4


def test_tiers():
    t = m.tiers()
    assert [r(x.venue_annual, 3) for x in t] == [0.036, 0.45, 0.946] and [r(x.annual, 3) for x in t] == [0.286, 1.35, 4.446]


def test_choices():
    c = m.choices()
    assert [v["best"] for v in c.values()] == [2, 2, 0, 2, 1]
    assert [[r(x) for x in v["profits"]] for v in c.values()] == [
        [2.11, 1.05, 13.95], [0.31, -0.75, 9.65], [3.31, 3.25, 1.15], [3.71, 7.65, 19.55], [1.71, 3.05, -0.05]]


def test_races():
    rc = m.races()
    assert [v["profile"] for v in rc.values()] == [[2] * 5, [2] * 5, [1, 0, 0, 0, 0], [2, 2, 2, 2, 0], [1, 1, 0, 0, 0]]
    assert [r(v["spend"]) for v in rc.values()] == [22.23, 22.23, 2.49, 18.07, 3.56]
    assert [r(100 * v["wasted_share"], 1) for v in rc.values()] == [93.6, 93.6, 42.7, 92.1, 59.8]
    assert [r(v["industry_profit"]) for v in rc.values()] == [37.77, 7.77, 17.51, 21.93, 6.44]
    assert [r(v["baseline_profit"]) for v in rc.values()] == [58.57, 28.57, 18.57, 38.57, 8.57]
    ind = m.industry()
    assert (r(ind["spend"]), r(ind["baseline"]), r(100 * ind["wasted_share"], 1)) == (68.58, 7.15, 89.6)


def test_budget():
    _, (run, change, share) = m.budget()
    assert (r(run), r(change), r(100 * share, 1)) == (16.17, 4.0, 80.2)


def test_small_runs():
    s = tt.Strategy("x", 10.0, 0.5)
    assert tt.best_tier(s, m.tiers(), [0, 0])[0] in (0, 1, 2)


def test_exercises():
    s = m.STRATEGIES[0]
    assert r(tt.revenue(s, 2, [1, 1, 0, 0]), 1) == 50.4 and r(tt.revenue(s, 2, [2, 2, 1, 0]), 1) == 18.4
    t = m.tiers()
    assert [r(100 * x.venue_annual / x.annual, 1) for x in t] == [12.6, 33.3, 21.3]
    assert [int(a * v / d) for a, v, d in ((0.8, 60, 4.16), (0.5, 40, 4.16), (0.3, 10, 1.064), (0.1, 20, 1.064))] == [11, 4, 2, 1]
    assert r(4.16, 2) == r(t[2].annual - t[0].annual, 2) and r(1.064, 3) == r(t[1].annual - t[0].annual, 3)
    rc = m.races(other={"tier 3": 7.0})
    assert [v["profile"].count(2) for v in rc.values()] == [5, 3, 0, 2, 0]
    ind = m.industry(other={"tier 3": 7.0})
    assert (r(ind["spend"]), r(100 * ind["wasted_share"], 1)) == (86.94, 91.8)
    assert r(100 * (3239.3 - 2293.4) / 3239.3, 0) == 29 and r(100 * (212.0 / 213.8 - 1), 1) == -0.8
    assert r(100 * 7.77 / 28.57, 0) == 27
