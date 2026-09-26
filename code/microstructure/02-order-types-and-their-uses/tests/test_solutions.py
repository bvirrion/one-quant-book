"""Numbers gate: every numerical answer printed in Book 10, chapter 2 (text and solutions)."""
import functools
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_ordertypes import (  # noqa: E402
    free_option,
    iceberg_study,
    passive_markout,
    session,
    showcase,
    sigma_per_sqrt_second,
    stop_cascade,
)


def r(x, d=2):
    return round(float(x), d)


@functools.cache
def ice(mode, d, j, loose=False):
    return iceberg_study(mode, d, j, window_ms=1000, tol=0.35) if loose else iceberg_study(mode, d, j)


def test_showcase():
    rows = dict(showcase())
    assert [(v["reports"], v["filled"], v["reason"], v["displayed"]) for v in rows.values()] == [
        ("A", 0, "", 100), ("AE", 200, "", 0), ("J", 0, "O", 0), ("AC", 0, "I", 0), ("AEC", 300, "I", 0),
        ("A", 0, "", 100), ("A", 0, "", 0), ("A", 0, "", 0)]


def test_cascade():
    assert [stop_cascade(n)["drop_cents"] for n in (0, 10, 20)] == [5, 21, 37]
    assert [stop_cascade(n, limit_offset=1)["drop_cents"] for n in (10, 20)] == [15, 25]
    c = stop_cascade(20)
    assert (c["traded"], c["stops_triggered"]) == (19_000, 20)
    assert stop_cascade(20, limit_offset=1)["traded"] == 13_000


def test_iceberg():
    assert (r(ice("venue", 0, 0.0)["rate"]), ice("venue", 0, 0.0)["refills"], ice("venue", 0, 0.0)["false_alarms"]) == (
        1.0, 99, 20)
    assert [r(ice("algo", d, j)["rate"], 3) for d, j in ((0, 0.0), (200, 0.0), (200, 0.3))] == [0.625, 0.183, 0.056]
    assert [r(ice("algo", d, j, True)["rate"], 3) for d, j in ((0, 0.0), (200, 0.0), (200, 0.3))] == [0.852, 0.704, 0.472]
    assert ice("algo", 200, 0.3, True)["false_alarms"] == 378 and ice("algo", 200, 0.3, True)["detected"] == 34
    assert ice("venue", 0, 0.0)["sold"] == 30_000


def test_free_option():
    t = session()
    m = passive_markout(t)
    assert (r(m["all"]), r(m["informed"]), r(m["uninformed"]), r(100 * m["informed_share"], 1)) == (0.41, -1.22, 0.58, 9.2)
    s = sigma_per_sqrt_second(t)
    assert r(s) == 0.27 and r(free_option(0.5, s, 10.0), 3) == 0.146
    assert r(free_option(0.5, s, 60.0), 3) == 0.604 and r(free_option(0.0, 1.0, 1.0), 3) == 0.399


def test_exercises():
    # exercise 2: FOK 400 against 300 available -> cancelled; IOC 400 -> 300 filled, 100 cancelled
    assert (min(400, 300), 400 - 300) == (300, 100)
    # exercise 4: iceberg of 10,000 showing 500 fully executed: 20 slices, 19 refreshes
    assert (10_000 // 500, 10_000 // 500 - 1) == (20, 19)
    # exercise 5: free option of a quote 1 tick from value, sigma 0.5 tick/sqrt(s), 30 s
    assert r(free_option(1.0, 0.5, 30.0), 3) == 0.665


def test_exercise_7():
    f = iceberg_study("algo", 0, 0.0, follow=True)
    assert (r(f["rate"], 2), f["false_alarms"], f["sold"]) == (0.43, 13, 23_700)
