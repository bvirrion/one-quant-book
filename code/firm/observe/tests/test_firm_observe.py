"""Acceptance tests of firm.observe (One Quant Book 15, chapter 28)."""
import io
import json
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_observe as O  # noqa: E402


def test_registry_and_logs():
    r = O.Registry()
    r.counter("msgs", svc="cap").inc(3)
    r.counter("msgs", svc="cap").inc()
    r.gauge("age", svc="risk").set(0.2)
    for v in (1_000, 2_000, 1_000_000):
        r.histogram("lat", svc="risk").observe(v)
    assert r.counter("msgs", svc="cap").value == 4 and r.gauge("age", svc="risk").value == 0.2
    assert r.histogram("lat", svc="risk").h.count == 3
    with pytest.raises(TypeError):
        r.gauge("msgs", svc="cap")
    s = io.StringIO()
    O.log(s, 1.5, "WARN", "risk", "stale", trace="t1", span="s2", age=7.0)
    assert json.loads(s.getvalue()) == {"ts": 1.5, "level": "WARN", "service": "risk", "event": "stale",
                                        "trace": "t1", "span": "s2", "age": 7.0}


def test_tracer():
    tr = O.Tracer()
    root = tr.start("msg", "feed", 0.0)
    a = tr.start("capture", "cap", 0.0, parent=root)
    tr.finish(a, 0.1)
    b = tr.start("risk", "risk", 0.1, parent=root)
    tr.finish(b, 0.5)
    tr.finish(root, 0.5)
    spans = tr.trace(root.trace_id)
    assert [s.name for s in spans] == ["msg", "capture", "risk"] and {s.parent_id for s in spans[1:]} == {root.span_id}
    assert len({s.trace_id for s in spans}) == 1


def test_slo_and_pages():
    slo = O.SLO(0.999, 30 * 86400)
    assert slo.budget(1_000_000) == pytest.approx(1000) and slo.burn_rate(0.0144) == pytest.approx(14.4)
    assert O.error_budget_used(50, 100_000, 0.999) == pytest.approx(0.5)
    v = np.zeros(10_000)
    v[100:110] = 10
    v[5000:5003] = 10
    assert O.threshold_pages(v, 5, min_gap_s=1000) == [100, 5000]
    assert O.threshold_pages(v, 5, min_gap_s=10_000) == [100]
    bad = np.zeros(20_000, dtype=bool)
    bad[10_000:] = True                                   # an outage starting at 10,000 s
    p = O.burn_rate_pages(bad, 0.999, [(3600, 300, 14.4)])
    assert p == [10_000 + 51]              # the 52nd bad second: 1.44% of an hour is 51.8 seconds
    assert O.burn_rate_pages(bad[:10_030], 0.999, [(3600, 300, 14.4)]) == []


def test_timeline():
    ev = O.timeline([(5, "alert", "b")], [(1, "log", "a"), (5, "log", "c")])
    assert [e[2] for e in ev] == ["a", "b", "c"]
