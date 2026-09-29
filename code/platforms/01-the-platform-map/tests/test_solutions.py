"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 1 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "platmap"))
from firm_platmap import Job, PlatformMap, hhmm
from pl_platmap import DEADLINE, HOOK_NIGHT, SYSTEMS, datasets, draft, firm, jobs, latest_arrivals


def hm(pair):
    return tuple(hhmm(x) for x in pair)


def test_small_runs():
    m = firm()
    assert m.validate() == [] and len(SYSTEMS) == 18 and len(m.datasets) == 22 and len(m.jobs) == 15
    assert sum(d.ready is not None for d in m.datasets) == 7
    assert draft().validate() == ["marks: 2 systems of record (pricing library, product control)"]


def test_nominal_night():
    m = firm()
    s = m.schedule()
    assert hm(s["golden copy"]) == ("19:30", "19:55") and hm(s["positions"]) == ("19:55", "20:15")
    assert hm(s["risk batch"]) == ("20:15", "02:15") and hm(s["pnl"]) == ("20:15", "20:40")
    assert max(e for _, e in s.values()) == 715 and hhmm(715) == "03:55"
    assert m.longest_chain() == ["golden copy", "features", "backtests"]
    assert DEADLINE - 715 == 185
    sl = m.slack(DEADLINE)
    assert sl["risk batch"] == 285 and hhmm(m.latest_starts(DEADLINE)["risk batch"]) == "01:00"
    lat = latest_arrivals(m)
    assert {k: hhmm(v) for k, v in lat.items()} == {
        "fills": "00:40", "capture": "22:25", "closing prices": "00:40", "snapshot": "00:20",
        "vendor reference": "22:35", "vendor corporate actions": "22:35", "clearing statement": "05:50"}
    margins = {d.name: lat[d.name] - d.ready for d in m.datasets if d.ready is not None}
    assert margins == {"fills": 515, "capture": 380, "closing prices": 500, "snapshot": 455,
                       "vendor reference": 275, "vendor corporate actions": 185, "clearing statement": 500}
    assert max(margins, key=margins.get) == "fills"
    # the risk branch alone: file -> golden copy -> positions -> risk batch
    assert 210 + 25 + 20 + 360 == 615 < 715


def test_blast_radius():
    m = firm()
    assert m.blast_radius() == {"fills": 9, "capture": 4, "closing prices": 4, "snapshot": 5, "vendor reference": 9,
                                "vendor corporate actions": 9, "clearing statement": 2}
    assert m.downstream("clearing statement") == {"breaks", "signed pnl"}
    assert len(m.downstream("vendor corporate actions")) == 9


def test_hook_night():
    fixed = firm(risk_start=300)
    assert fixed.stale_reads() == []
    st = fixed.stale_reads(HOOK_NIGHT)
    assert [(j, d, hhmm(s), hhmm(r)) for j, d, s, r in st] == [
        ("risk batch", "positions", "21:00", "22:15"), ("risk batch", "security master", "21:00", "21:55")]
    assert hm(fixed.schedule(HOOK_NIGHT)["pnl"]) == ("22:15", "22:40")
    # threshold: positions ready 45 minutes after the file
    assert 300 - 45 == 255 and hhmm(255) == "20:15" and 255 - 210 == 45
    dep = firm()
    assert dep.stale_reads(HOOK_NIGHT) == []
    s = dep.schedule(HOOK_NIGHT)
    assert hm(s["risk batch"]) == ("22:15", "04:15") and DEADLINE - s["risk batch"][1] == 165
    assert hhmm(s["backtests"][1]) == "05:55"


def test_exercises():
    m = firm()
    # 2: vendor reference at 22:50
    s = m.schedule({"vendor reference": 410})
    late = {j: e - DEADLINE for j, (_, e) in s.items() if e > DEADLINE}
    assert late == {"backtests": 15}
    assert hm(s["risk batch"]) == ("23:35", "05:35") and hhmm(s["features"][1]) == "01:15"
    ls = m.latest_starts(DEADLINE)
    assert (hhmm(ls["features"]), hhmm(ls["backtests"]), hhmm(ls["positions"])) == ("23:00", "01:00", "00:40")
    # 4: fixed start 20:30
    fx = firm(risk_start=270)
    assert fx.stale_reads() == [] and fx.stale_reads({"vendor corporate actions": 226}) != []
    assert fx.stale_reads({"vendor corporate actions": 225}) == []
    assert hhmm(225) == "19:45" and 225 - 210 == 15
    # 7: margin forecast
    js = jobs() + [Job("margin forecast", ("positions", "clearing statement"), ("margin forecast",), 60, deadline=840)]
    ds = datasets()
    from firm_platmap import Dataset
    m7 = PlatformMap(SYSTEMS, ds + [Dataset("margin forecast", "risk grid")], js)
    assert m7.validate() == []
    l7, l0 = m7.latest_starts(DEADLINE), m.latest_starts(DEADLINE)
    assert l7["margin forecast"] == 780 and hhmm(780) == "05:00"
    assert all(l7[k] == l0[k] for k in l0)
    assert latest_arrivals(m7)["clearing statement"] == 780
    # 8: halve the risk batch
    js8 = [Job(j.name, j.inputs, j.outputs, 180 if j.name == "risk batch" else j.duration) for j in jobs()]
    s8 = PlatformMap(SYSTEMS, datasets(), js8).schedule()
    assert hhmm(s8["risk batch"][1]) == "23:15" and max(e for _, e in s8.values()) == 715
