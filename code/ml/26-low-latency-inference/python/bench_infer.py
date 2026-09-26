"""Measured data for Book 12, chapter 26 (run once, by hand, under nice; never by make figdata): single-call latency of
the forest and the int8 MLP through Python, LightGBM, C++20 and Rust, and LightGBM's latency against batch size.
Writes figdata/ml/26-low-latency-inference/measured_latency.csv, measured_batch.csv and their .meta sidecars."""
import datetime
import os
import pathlib
import platform
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "mlinfer"))
import firm_mlinfer as mi  # noqa: E402
import ml_infer as m  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[4]
OUT = ROOT / "figdata" / "ml" / "26-low-latency-inference"
FIRM = ROOT / "code" / "firm" / "mlinfer"


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
    rustc = subprocess.run(["rustc", "--version"], capture_output=True, text=True).stdout.strip()
    d = {"cpu": cpu, "logical_cpus": os.cpu_count(), "kernel": platform.release(), "python": platform.python_version(),
         "gxx": gxx + " (-O2)", "rustc": rustc + " (--release)", "torch": torch.__version__, "torch_threads": 1,
         "loadavg_1_5_15": " ".join(f"{x:.2f}" for x in os.getloadavg()),
         "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "nice": os.nice(0), "isolated_cores": "none",
         "shared": "yes: other jobs may have run on the machine",
         "source": "code/ml/26-low-latency-inference/python/bench_infer.py"}
    return "".join(f"{k}: {v}\n" for k, v in d.items())


def main():
    torch.set_num_threads(1)
    OUT.mkdir(parents=True, exist_ok=True)
    forest, mlp, _, X = m.models()
    V = np.loadtxt(FIRM / "data" / "vectors.csv", delimiter=",")[:, :16]
    rows = [v[None, :].copy() for v in V]
    trows = [torch.as_tensor(r, dtype=torch.float32) for r in rows]
    f = mi.export_forest(forest)
    q = mi.quantise(mlp, X[:2000])
    res = [("LightGBM predict (Python)", *time_calls(forest.predict, rows, 5000)),
           ("exported forest in Python", *time_calls(lambda x: mi.forest_predict(f, x), rows, 300)),
           ("float MLP in PyTorch", *time_calls(lambda x: mlp(x), trows, 5000)),
           ("int8 MLP in NumPy", *time_calls(lambda x: mi.int8_forward(q, x), rows, 5000))]
    exe = FIRM / "cpp" / "bin" / "mlinfer_bench"
    subprocess.run(["g++", "-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror", f"-I{FIRM / 'cpp'}",
                    str(FIRM / "cpp" / "mlinfer_bench.cpp"), "-o", str(exe)], check=True)
    for line in subprocess.run([str(exe)], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines():
        name, *v = line.split(",")
        res.append((name, *map(float, v)))
    for line in subprocess.run(["cargo", "run", "-q", "--release", "--bin", "bench"], cwd=FIRM / "rust",
                               capture_output=True, text=True, check=True).stdout.splitlines():
        name, *v = line.split(",")
        res.append((name, *map(float, v)))
    with open(OUT / "measured_latency.csv", "w") as fh:
        fh.write("i,path,median_ns,p99_ns,p999_ns\n")
        for i, (name, a, b, c) in enumerate(res):
            fh.write(f"{i},{name},{a:.0f},{b:.0f},{c:.0f}\n")
    with open(OUT / "measured_batch.csv", "w") as fh:
        fh.write("batch,call_us,per_row_us\n")
        for b in (1, 4, 16, 64, 256, 1024):
            Xb = [np.tile(V[:1], (b, 1)) + 0.0 for _ in range(50)]
            med = time_calls(forest.predict, Xb, 400)[0] / 1e3
            fh.write(f"{b},{med:.1f},{med / b:.3f}\n")
    for name in ("measured_latency.csv", "measured_batch.csv"):
        (OUT / (name + ".meta")).write_text(meta())


if __name__ == "__main__":
    main()
