"""Acceptance tests of firm.platmap (One Quant Book 15, chapter 1)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_platmap import Dataset, Job, PlatformMap, System, hhmm


def small(start_c=None):
    s = [System("feed", "venue"), System("store", "data"), System("risk", "risk")]
    d = [Dataset("raw", "feed", "stream", ready=5), Dataset("ref", "store", ready=100),
         Dataset("clean", "store"), Dataset("report", "risk")]
    j = [Job("a", ("raw",), ("clean",), 30), Job("c", ("clean", "ref"), ("report",), 60, start=start_c)]
    return PlatformMap(s, d, j)


def test_forward_pass_and_longest_chain():
    m = small()
    assert m.validate() == []
    assert m.schedule() == {"a": (5, 35), "c": (100, 160)}
    assert m.longest_chain() == ["c"]
    assert m.schedule({"raw": 90})["c"] == (120, 180)
    assert m.longest_chain({"raw": 90}) == ["a", "c"]


def test_backward_pass_and_slack():
    m = small()
    assert m.latest_starts(900) == {"c": 840, "a": 810}
    assert m.slack(900) == {"a": 805, "c": 740}


def test_stale_read_of_fixed_start_job():
    m = small(start_c=50)
    assert m.stale_reads() == [("c", "ref", 50, 100)]
    assert small().stale_reads() == []


def test_validation_finds_conflicts_and_cycles():
    s = [System("x", "l"), System("y", "l")]
    d = [Dataset("p", ("x", "y"), ready=0), Dataset("q", "x"), Dataset("r", "x"), Dataset("orphan", "z")]
    j = [Job("j1", ("p", "r"), ("q",), 1), Job("j2", ("q",), ("r",), 1)]
    probs = PlatformMap(s, d, j).validate()
    assert any("2 systems of record" in p for p in probs)
    assert any("unknown system z" in p for p in probs)
    assert any("orphan: no producer" in p for p in probs)
    assert any(p.startswith("cycle") for p in probs)


def test_closures_and_blast_radius():
    m = small()
    assert m.downstream("raw") == {"clean", "report"}
    assert m.upstream("report") == {"clean", "ref", "raw"}
    assert m.blast_radius() == {"raw": 2, "ref": 1}
    assert hhmm(0) == "16:00" and hhmm(900) == "07:00" and hhmm(485) == "00:05"
