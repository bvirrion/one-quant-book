"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 24 (text and solutions)."""
import csv
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import pl_eventlog as P

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/platforms/24-messaging-and-event-driven-architecture"


def _csv(name):
    return list(csv.DictReader(open(FIG / name)))


def test_small_runs():
    r = {m: P.schedules(m, days=3, n=2_000) for m in P.MODES}
    assert r["at-most-once"]["lost"] > 0 and r["at-most-once"]["dup"] == 0
    assert r["at-least-once"]["dup"] > 0 and r["at-least-once"]["lost"] == 0
    assert (r["atomic"]["lost"], r["atomic"]["dup"], r["atomic"]["max_error"]) == (0, 0, 0)
    i = P.schedules("idempotent", days=3, n=2_000)                    # exercise 7
    assert (i["lost"], i["dup"], i["max_error"]) == (0, 0, 0)


def test_fills_and_publishing():
    fs = P.fills()
    assert len(fs) == 10_000 and sum(abs(f["qty"]) for f in fs[:3]) > 0
    assert P.publishing("write-then-publish") == {"lost": 22, "phantom": 0, "duplicated": 0}
    assert P.publishing("publish-then-write") == {"lost": 0, "phantom": 22, "duplicated": 0}


def test_csvs():
    m = {r["mode"]: r for r in _csv("modes.csv")}
    assert [(m[k]["crashes"], m[k]["lost"], m[k]["duplicated"], m[k]["max_error"], m[k]["median_error"]) for k in P.MODES] == [
        ("967", "48662", "0", "5100", "3500"), ("1000", "0", "48652", "6500", "3800"), ("1000", "0", "0", "0", "0")]
    assert (m["at-most-once"]["lost_per_1000"], m["at-least-once"]["dup_per_1000"]) == ("50323", "48652")
    o = {r["design"]: (r["lost"], r["phantom"], r["duplicated"]) for r in _csv("outbox.csv")}
    assert o == {"write-then-publish": ("22", "0", "0"), "publish-then-write": ("0", "22", "0"),
                 "outbox-no-idempotence": ("0", "0", "22"), "outbox": ("0", "0", "0")}


@pytest.mark.reference
def test_full_schedules():
    r = P.schedules("at-least-once")
    assert (r["crashes"], r["dup"], r["max_error"]) == (1000, 48652, 6500)
    assert P.publishing("outbox") == {"lost": 0, "phantom": 0, "duplicated": 0}
