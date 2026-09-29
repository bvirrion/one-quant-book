import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_serverspec as ss  # noqa: E402


def test_latency_model():
    assert ss.path_ns(1000, 1.0, 5.0, 2.5) == pytest.approx(500)
    assert ss.path_ns(1000, 0.0, 5.0, 2.5) == pytest.approx(1000)            # memory-bound: no gain
    assert ss.speedup(0.5, 5.0, 2.5) == pytest.approx(1 / 0.75)
    assert ss.path_ns(1000, 0.6, 4.8, 4.8) == pytest.approx(1000)


def test_cabinet_fit_and_rank():
    c = ss.CANDIDATES[0]
    assert c.server_w == 570 and ss.per_cabinet(c, 10) == 17 and ss.per_cabinet(c, 100) == 42
    r = ss.rank(1528, 0.6, 4.8, 10)
    assert r[0]["name"] == "AMD EPYC 9175F" and r[0]["path_ns"] < r[-1]["path_ns"]
    assert all(x["servers"] >= 0 for x in r)


def test_firmware_audit_uses_tuneaudit_findings():
    f = ss.firmware_audit({"cstates": "disabled", "smt": "enabled"})
    by = {x.rule: x.status for x in f}
    assert by["firmware:cstates"] == "ok" and by["firmware:smt"] == "fail" and by["firmware:turbo"] == "unknown"
    assert "firmware:cstates" in ss.ta.report(f)
