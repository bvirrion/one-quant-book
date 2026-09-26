"""Numbers gate: every numerical answer printed in Book 12, chapter 29 (text and solutions). One run of the whole
pipeline (about three minutes on one core) serves every test."""
import pathlib
import sys
import tempfile

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_lobmodel as m  # noqa: E402


def test_setup_and_data():
    c = m.CFG
    assert (len(c["train"]), len(c["valid"]), len(c["test"]), c["seconds"]) == (8, 3, 6, 1200.0)
    assert not set(c["train"]) & set(c["valid"]) and not set(c["valid"]) & set(c["test"])
    s = m.summary()
    assert (s["train rows"], s["valid rows"]) == (51924, 33457) and round(s["zero moves"], 3) == 0.894
    assert round(s["tick moves"], 3) == 0.052 and round(2 * 0.5 + 2 * 0.003 / 0.01, 1) == 1.6
    assert [round(x, 3) for x in s["cv"]] == [0.558, 0.555, 0.548] and s["chosen leaves"] == 7
    assert (s["trees"], s["nodes"]) == (150, 900)
    assert (round(s["valid ic"], 3), round(s["train ic"], 3), round(s["tcn ic"], 3)) == (0.522, 0.625, 0.452)
    assert s["tcn params"] == 12867 and s["parity"] == 0.0


def test_measured_latencies_and_grid():
    t = m.measured()
    assert t["cpp forest branches"] < t["cpp forest loop"] < t["flat forest (Python and NumPy)"]
    assert t["flat forest (Python and NumPy)"] < t["TCN forward (PyTorch one window)"] < t["LightGBM predict (Python)"]
    assert round(t["cpp forest branches"], -1) == m.CFG["decision_ns"] == m.CFG["latencies"][1] == 150
    assert round(t["LightGBM predict (Python)"], -3) == m.CFG["latencies"][2] == 263_000
    assert round(t["LightGBM predict (Python)"] / t["cpp forest branches"], -2) == 1700
    assert (round(t["cpp forest loop"] / 1000, 1), round(t["TCN forward (PyTorch one window)"] / 1000)) == (1.1, 166)


def test_threshold_choice():
    s = m.summary()
    assert [round(x, 1) for x in s["threshold pnl"]] == [43.4, 53.9, 48.0, 50.1] and s["threshold"] == 0.1


def test_latency_table():
    rows, base = m.latency_table()
    got = [(round(r["pnl"], 2), round(r["markout 1 s"], 3), r["positive sessions"]) for r in rows]
    assert got[:3] == [(21.73, 0.405, 6)] * 3
    assert got[3:] == [(21.23, 0.399, 6), (21.72, 0.405, 6), (20.63, 0.394, 6), (20.52, 0.417, 6), (12.4, 0.353, 6),
                       (1.6, 0.245, 3), (-12.27, 0.148, 2)]
    assert round(rows[1]["se"], 2) == 3.9 and round(rows[1]["entries"], 1) == 34.3 and round(rows[1]["fees"], 2) == -6.73
    assert [round(r["staleness ms"], 2) for r in rows][:2] == [0.02, 0.02]
    assert (round(rows[8]["staleness ms"]), round(rows[9]["staleness ms"])) == (154, 802)
    assert (round(rows[1]["markout 0.1 s"], 3), round(rows[9]["markout 0.1 s"], 3)) == (0.447, 0.27)
    assert (round(base["pnl"], 2), round(base["se"], 2), round(base["markout 1 s"], 3)) == (5.47, 2.22, 0.078)
    assert (round(base["entries"], 1), round(base["fees"], 2)) == (58.7, -14.63)
    assert (round(m.zero_crossing()), round(m.zero_crossing(level=base["pnl"]))) == (106, 89)
    assert round(rows[1]["pnl"] / base["pnl"], 1) == 4.0


def test_tracking_and_monitors():
    with tempfile.TemporaryDirectory() as d:
        rid, lineage, broken = m.tracking(d)
    assert len(rid) == 16 and broken == -1 and set(lineage) == {"run", "artefact", "data", "code"}
    mon = m.monitors()
    assert [x["decisions"] for x in mon] == [7620, 4351, 5539, 5747, 3974, 3373]
    assert [round(x["max"], 2) for x in mon] == [0.14, 0.3, 0.64, 0.42, 1.36, 1.6]
    assert {x["feature"] for x in mon} == {"updates 1 s", "trades 5 s"}
    assert round(max(x["price max"] for x in mon), 2) == 0.13 and round(min(x["price max"] for x in mon), 2) == 0.02
    rate = np.array([x["decisions"] for x in mon]) / m.CFG["seconds"]
    assert (round(rate.min(), 1), round(rate.max(), 1), round(rate.mean(), 1)) == (2.8, 6.4, 4.3)


def test_scaling_arithmetic():
    rate = np.mean([7620, 4351, 5539, 5747, 3974, 3373]) / 1200.0
    assert round(106 * rate / 2000, 2) == 0.23 and round(166 / 0.153, -2) == 1100 and round(0.106 * rate, 2) == 0.45
