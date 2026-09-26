"""Numbers gate, Book 13 chapter 25."""
import csv
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
FIG = ROOT / "figdata/low-latency/25-testing-and-deploying-low-latency-systems"
sys.path.insert(0, str(ROOT / "code/firm/perfgate"))
import firm_perfgate as pg  # noqa: E402


def rows(name):
    with open(FIG / name, newline="", encoding="utf8") as f:
        return list(csv.DictReader(f))


def summary():
    return {r["key"]: float(r["value"]) for r in rows("gate_summary.csv")}


def test_exercises():
    assert round(pg.runs_needed(0.14, 0.10)) == 53 and round(pg.runs_needed(0.14, 0.025), -1) == 840
    assert 20 * 21 == 420 and round(420 * 0.05) == 21 and round(420 * 0.03) == 13 and round(420 * 0.09) == 38
    assert (ord("0") - ord("1")) + (ord("3") - ord("2")) == 0
    assert len(json.loads((ROOT / "code/firm/perfgate/data/cert_script.json").read_text())) == 17


def test_gate_numbers():
    s = summary()
    assert round(s["median_p99_a_ns"]) == 208 and round(s["median_p99_b_ns"]) == 245
    assert round(s["planted_rise"] * 100) == 18 and round(s["robust_cv"] * 100) == 14
    assert round(s["runs_needed_5pct_90pct"], -1) == 220
    g = {int(r["runs"]): r for r in rows("gate.csv")}
    fa = [float(r["false_alarm"]) for r in g.values()]
    assert (min(fa), max(fa)) == (0.03, 0.09)
    assert float(g[40]["detect_planted"]) == 0.99
    assert [float(g[n]["detect_5pct"]) for n in (80, 120, 160, 200)] == [0.57, 0.73, 0.84, 0.91]
    assert float(g[160]["detect_5pct"]) < 0.9 <= float(g[200]["detect_5pct"])       # about 200 runs per side
    assert round(2 * 200 * 0.030) == 12
    assert round(pg.runs_needed(0.05, 0.05)) == 27
    meta = (FIG / "measured_gate_runs.csv.meta").read_text()
    assert "planted_wait_ns: 11.4" in meta and len(rows("measured_gate_runs.csv")) == 800


def test_fuzz_numbers():
    r = rows("measured_fuzz.csv")
    real = [x for x in r if x["target"] == "real"][0]
    assert real["iterations"] == "1000000"
    trusting = [x for x in r if x["target"] == "trusting"]
    assert len(trusting) == 10 and all(x["result"] == "heap-buffer-overflow" for x in trusting)
    assert max(int(x["iterations"]) for x in trusting) == 12
