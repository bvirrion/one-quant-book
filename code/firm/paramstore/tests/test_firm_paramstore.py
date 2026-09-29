"""Acceptance tests of firm.paramstore (One Quant Book 15, chapter 16)."""
import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_paramstore as S  # noqa: E402

SCH = S.Schema("lim", "fraction", {"bp": 1e-4, "percent": 1e-2}, lo=0.0, hi=0.02, max_step=0.005,
               two_approvals_above=0.002)


def store(tmp_path):
    s = S.ParamStore(tmp_path)
    s.register(SCH)
    return s


def test_units_bounds_and_steps(tmp_path):
    s = store(tmp_path)
    ok = s.propose("a", "lim", 50, "bp", 0, 0, "u")
    assert ok.status == "pending" and ok.value == pytest.approx(0.005) and ok.needed == 1
    assert s.propose("a", "lim", 50, "", 0, 0, "u").status == "refused"
    bad = s.propose("a", "lim", 50, "percent", 0, 0, "u")
    assert bad.status == "refused" and any("outside" in r for r in bad.reasons)


def test_approvals(tmp_path):
    s = store(tmp_path)
    c = s.propose("a", "lim", 10, "bp", 0, 0, "u")                 # a step of 0.001: one approval
    s.approve(c.cid, "u", 1)
    assert c.status == "pending"                                     # the author cannot approve
    s.approve(c.cid, "v", 2)
    assert c.status == "applied" and s.as_of("a", "lim", 5) == pytest.approx(0.001)
    d = s.propose("a", "lim", 50, "bp", 10, 10, "u")                 # a step of 0.004: two approvals
    s.approve(d.cid, "v", 11)
    s.approve(d.cid, "v", 12)
    assert d.status == "pending"
    s.approve(d.cid, "w", 13)
    assert d.status == "applied" and d.approvals == ["v", "w"]
    big = s.propose("a", "lim", 150, "bp", 20, 20, "u")              # 0.015 - 0.005 > max_step
    assert big.status == "refused" and any("step" in r for r in big.reasons)


def test_bitemporal_history_and_audit(tmp_path):
    s = store(tmp_path)
    for v, eff, rec, who in ((10, 0, 0, "v"), (20, 100, 100, "v"), (15, 50, 200, "w")):
        c = s.propose("a", "lim", v, "bp", eff, rec, "u")
        s.approve(c.cid, who, rec)
    assert s.as_of("a", "lim", 60, known=150) == pytest.approx(0.001)
    assert s.as_of("a", "lim", 60) == pytest.approx(0.0015) and s.as_of("a", "lim", 150) == pytest.approx(0.002)
    assert [round(r[2], 4) for r in s.history("a", "lim")] == [0.001, 0.0015, 0.002]
    assert s.audit.verify() == -1
    p = tmp_path / "audit.jsonl"
    lines = p.read_text().splitlines()
    rec = json.loads(lines[2])
    rec["body"]["entered"] = "99 bp"
    lines[2] = json.dumps(rec)
    p.write_text("\n".join(lines) + "\n")
    assert S.ParamStore(tmp_path).audit.verify() >= 0


def test_flags_drift_and_signals():
    f = S.Flags()
    f.set("x", ["a"])
    assert f.on("x", "a") and not f.on("x", "b") and not f.on("y", "a")
    assert S.drift({"a": {"p": 1.0}}, {"a": {"p": 1.0}, "b": {"p": 2.0}}) == [("b", "p", None, 2.0)]
    svc = S.SignalService(10.0, fallback=-1.0)
    svc.publish("s", 1.0, "v1", 0.0)
    svc.publish("s", 2.0, "v2", 5.0)
    assert svc.get("s", 6.0) == (2.0, "v2", "fresh") and svc.get("s", 16.0) == (-1.0, "v2", "stale-fallback")
    assert svc.get("s", 2.0) == (1.0, "v1", "fresh") and svc.get("t", 0.0) == (-1.0, None, "missing-fallback")
