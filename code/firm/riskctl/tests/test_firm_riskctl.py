import copy
import json
import math
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_riskctl as rc  # noqa: E402
from riskctl_fixture import LIMITS  # noqa: E402


def test_validate_and_export():
    assert rc.validate(LIMITS) == []
    bad = copy.deepcopy(LIMITS)
    bad["desks"]["etf_mm"]["max_gross_usd"] = 2e9
    bad["strategies"]["etf_arb"]["desk"] = "nowhere"
    errs = rc.validate(bad)
    assert any("exceeds the firm" in e for e in errs) and any("unknown desk" in e for e in errs)
    with pytest.raises(ValueError):
        rc.export(bad)
    g = rc.to_riskgate(LIMITS)
    assert g["firm"]["max_gross"] == 1_000_000_000 * rc.SCALE and g["instruments"][2]["max_notional"] == 400_000 * rc.SCALE
    assert g["strategies"]["quoter_a"] == {"desk": "equity_mm", "rate": 500, "burst": 50, "max_open": 400}


def test_fixture_is_what_riskgate_replays():
    d = json.loads((HERE / "data" / "limits.json").read_text())
    assert d == json.loads(json.dumps(rc.export(LIMITS), sort_keys=True))
    gate_dir = HERE.parent / "riskgate"
    if not (gate_dir / "firm_riskgate.py").exists():
        pytest.skip("firm.riskgate (Book 13) not present")
    sys.path.insert(0, str(gate_dir))
    import firm_riskgate as rg
    lim = rg.from_riskctl(d)
    g = rg.Gate(lim, 0)
    g.set_reference(0, 1, 40 * rc.SCALE)
    assert g.check(1, "quoter_a", 1, "B", 100, 40 * rc.SCALE + 10, 1)[0] == "."
    assert g.check(2, "quoter_a", 1, "B", 100, 50 * rc.SCALE, 2)[0] == "C"          # 25% above: outside the collar


def test_monitor_and_kill_switch():
    sw = rc.KillSwitch()
    m = rc.Monitor(LIMITS, sw)
    m.on_fill(0.0, "quoter_b", 1, 10000, 40.0)
    assert m.mark(1.0, {1: 39.0}) == []                      # -$10,000
    acts = m.mark(2.0, {1: -10.0})                           # -$500,000 exactly is not beyond the limit
    assert acts == []
    acts = m.mark(3.0, {1: -11.0})
    assert ("strategy", "quoter_b", "flatten") in acts and sw.blocks("quoter_b", "equity_mm")
    assert not sw.blocks("etf_arb", "etf_mm")
    sw.unkill(4.0, "strategy", "quoter_b")
    assert [a[1] for a in sw.audit] == ["kill", "unkill"]
    for i in range(5001):
        out = m.on_message(10.0 + i * 1e-4, "quoter_a")
    assert out == [("firm", "", "cancel")] and sw.blocks("anything", "etf_mm")


def test_runaway_and_normal_days():
    base = rc.runaway({})
    assert base["seconds"] == 2700 and math.isclose(base["orders"], 1481 * 2700)
    stop = rc.runaway({"loss": 2e6, "position": 2.5e8, "human_s": 300})
    assert stop["stopped_by"] == "loss limit" and stop["loss"] < 3e6
    assert rc.runaway({"throttle": 500})["loss"] < base["loss"]
    fa = rc.normal_days({"throttle": 500, "loss": 2e6})
    assert fa["throttle"] > 0.05 and fa["loss limit"] < 0.001
