"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 7 (text and solutions)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import pl_dataqual as P


def r(x, d=2):
    return round(float(x), d)


def test_small_runs(tmp_path):
    kw = {"hours": 0.02, "gen": str(tmp_path)}
    a, n = P.score(0, True, **kw), P.score(0, False, **kw)
    rules = [k for k in a if k != "vendor trade count"]
    assert all(a[k]["found"] == a[k]["planted"] for k in rules)
    assert all(a[k]["false"] <= n[k]["false"] for k in rules)


@pytest.mark.reference
def test_day_and_detection():
    e, q, t, halts = P.base()
    assert (len(e), len(q), len(t)) == (47472, 9258, 1190) and (halts[0][2] - halts[0][1]) // 10**9 == 60
    naive, aware = P.detection(20, False), P.detection(20, True)
    for rule, (planted, found) in {"sequence": (20, 20), "crossed book": (60, 60), "price spike": (160, 160),
                                   "stale quotes": (20, 20), "broken trades": (80, 80)}.items():
        assert (naive[rule]["planted"], naive[rule]["found"]) == (planted, found) == (aware[rule]["planted"],
                                                                                      aware[rule]["found"])
        assert aware[rule]["false"] == 0
    assert naive["price spike"]["false"] == 495 and naive["stale quotes"]["false"] == 20
    assert naive["vendor trade count"]["flags"] == 16
    s0n, s0a = P.score(0, False), P.score(0, True)
    assert (s0n["price spike"]["false"], s0n["stale quotes"]["false"]) == (24, 1)
    assert (s0a["price spike"]["false"], s0a["stale quotes"]["false"]) == (0, 0)


@pytest.mark.reference
def test_effect_and_lineage():
    e = P.effect(0)
    err = {s: 100 * (e["kept"][s]["vwap"] / e["truth"][s]["vwap"] - 1) for s in ("SIM1", "SIM2")}
    fl = {s: 100 * (e["flagged_out"][s]["vwap"] / e["truth"][s]["vwap"] - 1) for s in ("SIM1", "SIM2")}
    assert (r(err["SIM1"]), r(err["SIM2"])) == (2.69, 1.08)
    assert all(abs(v) < 0.03 for v in fl.values()) and r(fl["SIM2"]) == -0.02
    assert round(e["kept"]["SIM2"]["rv"] / e["truth"]["SIM2"]["rv"], -3) == 24000
    assert r(e["flagged_out"]["SIM2"]["rv"] / e["truth"]["SIM2"]["rv"], 6) == 1.0
    c = P.correction_and_lineage()
    assert (c["asof_night"], c["asof_morning"]) == (3004500, 3004300)
    assert c["stale"] == ["features 2026-09-22", "marks 2026-09-22", "pnl 2026-09-22"]
    assert c["untouched"] == ["bars 2026-09-22"]
    qz = P.quarantine_demo()
    assert qz.log[0][1] == "quarantined" and qz.log[-1][1] == "released"
    assert 91691 - 91686 - 1 == 4
