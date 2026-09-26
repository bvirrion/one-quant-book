"""Measured data for Book 12, chapter 29 (run once, by hand, under nice; never by make figdata): single-call latency
of the order-book model through LightGBM's Python call, the Python flat forest, a TCN call and the C++20 serving
path. Writes figdata/ml/29-build-an-order-book-model-end-to-end/measured_latency.csv and its .meta sidecar."""
import datetime
import os
import pathlib
import platform
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[4]
FIRM = ROOT / "code" / "firm" / "lobmodel"
sys.path.insert(0, str(FIRM))
import firm_lobmodel as lm  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
from firm_gbdt import make  # noqa: E402
from firm_lobseq import TCN  # noqa: E402

OUT = ROOT / "figdata" / "ml" / "29-build-an-order-book-model-end-to-end"


def pct(t):
    t = np.sort(np.asarray(t))
    return [float(t[int(q * (len(t) - 1))]) for q in (0.5, 0.99, 0.999)]


def time_calls(f, rows, n):
    out = []
    for k in range(n):
        x = rows[k % len(rows)]
        t0 = time.perf_counter_ns()
        f(x)
        out.append(time.perf_counter_ns() - t0)
    return pct(out)


def meta():
    cpu = next(ln.split(":", 1)[1].strip() for ln in open("/proc/cpuinfo") if ln.startswith("model name"))
    gxx = subprocess.run(["g++", "--version"], capture_output=True, text=True).stdout.splitlines()[0]
    d = {"cpu": cpu, "logical_cpus": os.cpu_count(), "kernel": platform.release(), "python": platform.python_version(),
         "gxx": gxx + " (-O2)", "torch": torch.__version__, "torch_threads": 1,
         "loadavg_1_5_15": " ".join(f"{x:.2f}" for x in os.getloadavg()),
         "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "nice": os.nice(0), "isolated_cores": "none",
         "shared": "yes: other jobs may have run on the machine",
         "source": "code/ml/29-build-an-order-book-model-end-to-end/python/bench_lobmodel.py"}
    return "".join(f"{k}: {v}\n" for k, v in d.items())


def main():
    torch.set_num_threads(1)
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        out, _ = lm.make_pipeline(d, lm.DEFAULT).run("fit")
    tr = out["train"]
    model = make(out["cv"]["chosen"], seed=1).fit(tr["X"], tr["y"])
    V = np.loadtxt(FIRM / "data" / "vectors.csv", delimiter=",")[:, :10]
    rows = [v[None, :].copy() for v in V]
    fp = lm.ForestPredictor(lm.read_forest(FIRM / "data" / "forest.txt"))
    torch.manual_seed(1)
    tcn = TCN(10).eval()
    win = [torch.as_tensor(np.repeat(r[None], 16, axis=1), dtype=torch.float32) for r in rows]

    def tcn_call(w):
        with torch.no_grad():
            return tcn(w)

    res = [("LightGBM predict (Python)", *time_calls(model.predict, rows, 5000)),
           ("flat forest (Python and NumPy)", *time_calls(lambda r: fp(r[0]), rows, 5000)),
           ("TCN forward (PyTorch one window)", *time_calls(tcn_call, win, 3000))]
    exe = FIRM / "cpp" / "bin" / "lobmodel_bench"
    exe.parent.mkdir(exist_ok=True)
    subprocess.run(["g++", "-std=c++20", "-O2", "-I", str(FIRM / "cpp"), str(FIRM / "cpp" / "lobmodel_bench.cpp"),
                    "-o", str(exe)], check=True)
    for line in subprocess.run([str(exe)], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines():
        name, *v = line.split(",")
        res.append((name, *map(float, v)))
    with open(OUT / "measured_latency.csv", "w") as f:
        f.write("path,median_ns,p99_ns,p999_ns\n")
        for name, a, b, c in res:
            f.write(f"{name},{a:.1f},{b:.1f},{c:.1f}\n")
    (OUT / "measured_latency.csv.meta").write_text(meta())


if __name__ == "__main__":
    main()
