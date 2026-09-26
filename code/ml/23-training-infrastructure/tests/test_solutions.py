"""Numbers gate: every numerical answer printed in Book 12, chapter 23 that does not depend on the machine; the measured
timings are checked only for the arithmetic the text does with them."""
import csv
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_train as m  # noqa: E402

MEASURED = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "ml" / "23-training-infrastructure" / "measured_loader.csv"


def test_data():
    assert [s.shape for s in m.sessions()] == [(1140, 41)] * 8
    sz = m.sizes()
    assert (round(sz["csv"] / 1e6, 2), round(sz["npy"] / 1e6, 2), round(sz["mmap"] / 1e6, 2)) == (2.21, 1.50, 1.50)
    assert 1140 - 20 - 10 + 1 == 1111
    assert m.gather_parity()


def test_precision():
    p = m.precision()
    assert (round(p["max diff"], 4), round(p["max rel diff"], 2), round(p["last 50 fp32"], 4), round(p["last 50 bf16"], 4)) == (
        0.0132, 0.23, 0.0527, 0.0525)
    assert round(p["last 50 fp32"] - p["last 50 bf16"], 4) == 0.0002
    assert (2.0**-7, round(2.0**-10, 5), round(2.0**-23 * 1e7, 1)) == (0.0078125, 0.00098, 1.2)


def test_parallel_and_resume():
    assert f"{m.accumulation():.1e}" == "1.4e-07"
    d, g = m.data_parallel()
    assert (f"{d:.1e}", round(g, 2)) == ("1.5e-08", 0.12)
    same, losses_same, size = m.resume()
    assert same and losses_same and round(size / 1e3) == 693
    assert round(m.naive_resume(), 3) == 0.039


def test_measured_arithmetic():
    rows = {r["format"]: r for r in csv.DictReader(open(MEASURED))}
    f = {k: {c: float(v[c]) for c in ("load_ms", "load_mb_s", "batch_ms", "compute_ms", "data_share")} for k, v in rows.items()}
    assert [round(f[k]["data_share"], 2) for k in ("csv", "npy", "mmap", "mmap-gather")] == [0.34, 0.31, 0.39, 0.20]
    assert f["csv"]["load_ms"] > f["npy"]["load_ms"] > f["mmap"]["load_ms"]
    assert f["mmap-gather"]["batch_ms"] < min(f[k]["batch_ms"] for k in ("csv", "npy", "mmap"))
    loop = f["mmap"]["batch_ms"] + f["mmap"]["compute_ms"]
    gath = f["mmap-gather"]["batch_ms"] + f["mmap-gather"]["compute_ms"]
    assert (round(loop, 2), round(loop / (f["mmap"]["batch_ms"] + f["mmap"]["compute_ms"] / 2), 2)) == (1.91, 1.44)
    assert (round(gath, 2), round(gath / (f["mmap-gather"]["batch_ms"] + f["mmap-gather"]["compute_ms"] / 2), 2)) == (1.37, 1.67)
    rows_year = 250 * 6.5 * 3600 / 0.5
    gb = rows_year * 41 * 4 / 1e9
    text = gb * m.sizes()["csv"] / m.sizes()["npy"]
    assert (round(rows_year / 1e6, 1), round(gb, 2), round(text, 1)) == (11.7, 1.92, 2.8)
    assert (round(text * 1e3 / f["csv"]["load_mb_s"]), round(gb * 1e3 / f["npy"]["load_mb_s"], 1)) == (16, 1.1)
    assert np.isfinite(f["mmap"]["load_ms"])
