"""Acceptance tests of firm.goldtest (One Quant Book 15, chapter 27)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_goldtest as G  # noqa: E402


def test_store_compare_and_approval(tmp_path):
    s = G.GoldenStore(tmp_path / "g.json")
    s.put(G.Golden("asian:1", 8.0, 0.1, {"engine": "MC"}))
    s.put(G.Golden("euro:1", 10.0, 1e-9))
    r = G.compare(s, {"asian:1": 8.05, "euro:1": 10.001, "euro:2": 1.0})
    assert [k for k, *_ in r.failures] == ["euro:1", "euro:2"] and r.by_product == {"euro": 1} and not r.ok
    s.propose("euro:1", 10.001, 1e-9, "day count fixed", by="ann")
    with pytest.raises(PermissionError):
        s.approve("euro:1", by="ann")
    s.approve("euro:1", by="bob")
    assert s.get("euro:1").provenance["approved_by"] == "bob"
    s.save()
    assert G.GoldenStore(tmp_path / "g.json").load().get("euro:1").value == 10.001
    assert G.compare(s, {"asian:1": 8.0, "euro:1": 10.001}).ok


def test_run_tiers_stops_at_first_failure():
    calls = []

    def ok():
        calls.append("a")
        return True

    def bad():
        calls.append("b")
        raise AssertionError("golden tier failed")

    res = G.run_tiers([("unit", ok), ("golden", bad), ("e2e", ok)])
    assert [(n, k) for n, _, k in res] == [("unit", True), ("golden", False)] and calls == ["a", "b"]


def test_release_train():
    s = G.release_train([0.5, 1.2, 1.9, 6.0], 7)
    assert s.batch_sizes == [4] and s.lead_days == pytest.approx([6.5, 5.8, 5.1, 1.0]) and s.bisect_steps == 2
    c = G.release_train([0.5, 1.2], 0)
    assert c.lead_days == [0, 0] and c.bisect_steps == 0
    assert math.isclose(G.release_train([1.0, 2.0, 3.0], 1).bisect_steps, 0.0)


def test_consistency_check():
    new, old, cfg = {"b": 2}, {"b": 1}, {"c": 1}
    rel = G.host_state(new, cfg)
    hosts = {f"h{i}": G.host_state(new, cfg) for i in range(3)}
    assert G.consistency(hosts, rel) == []
    hosts["h3"] = G.host_state(old, cfg)
    hosts["h4"] = G.host_state(new, {"c": 2})                   # configuration drift
    assert G.consistency(hosts, rel) == ["h3", "h4"]
