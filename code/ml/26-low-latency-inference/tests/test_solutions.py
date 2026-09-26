"""Numbers gate: every numerical answer printed in Book 12, chapter 26 that does not depend on the machine; measured
latencies are checked only for the orderings and arithmetic the text uses."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "mlinfer"))
import firm_mlinfer as mi  # noqa: E402
import ml_infer as m  # noqa: E402

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "ml" / "26-low-latency-inference"


def test_models_and_parity():
    a = m.accuracy()
    assert (round(a["forest"], 3), round(a["MLP float"], 3)) == (0.224, 0.182)
    assert tuple(round(x, 3) for x in a[8]) == (0.182, 0.179) and round(a[8][0], 4) == 0.1817
    assert tuple(round(x, 3) for x in a[6]) == (0.181, 0.176) and tuple(round(x, 3) for x in a[4]) == (0.143, 0.164)
    assert round(a["ptq error"], 3) == 0.045
    assert m.parity_python() == 0.0
    assert m.sizes() == {"trees": 300, "splits": 4200, "leaves": 4500, "mlp int8 bytes": 1236, "mlp float bytes": 4356}
    assert (round(a["MLP float"] - a[4][0], 3), round(a["MLP float"] - a[4][1], 3), round(a["MLP float"] - a[8][1], 3)) == (
        0.040, 0.018, 0.003)


def test_exercises():
    assert mi._multiplier(0.0123) == (1690499128, 37)
    assert (round(m.per_channel_ic(4), 3), round(m.per_channel_ic(8), 3)) == (0.153, 0.182)
    assert round(100 / 254, 2) == 0.39


def test_measured():
    rows = {r["path"]: r for r in csv.DictReader(open(FIG / "measured_latency.csv"))}
    med = {k: float(v["median_ns"]) for k, v in rows.items()}
    p99 = {k: float(v["p99_ns"]) for k, v in rows.items()}
    assert med["cpp forest branches"] < med["cpp forest loop"] < med["LightGBM predict (Python)"]
    assert med["cpp int8 mlp"] < med["cpp forest branches"]
    assert round(p99["cpp forest branches"] / p99["LightGBM predict (Python)"], 3) == 0.011
    assert round(med["rust forest"] / med["cpp forest loop"], 2) == 1.25
    b = {int(r["batch"]): (float(r["call_us"]), float(r["per_row_us"])) for r in csv.DictReader(open(FIG / "measured_batch.csv"))}
    assert b[1][1] > b[1024][1] and round(b[1024][0] / 1000, 1) == 3.1
    lines = (pathlib.Path(mi.__file__).parent / "cpp" / "forest_branches.hpp").read_text().count("\n")
    assert lines == 17107
