"""Measured data for Book 12, chapter 23 (run once, by hand, under nice; never by make figdata): where a training step's
time goes for each storage format. An epoch is 100 steps of batches of 256 windows; loading is what the format needs at
the start of each epoch (parse every CSV file, read every NumPy file, map the single file); batching is assembling a
batch of windows; compute is the forward pass, the backward pass and the optimiser step. Writes
figdata/ml/23-training-infrastructure/measured_loader.csv and its .meta sidecar."""
import datetime
import os
import pathlib
import platform
import time

import ml_train as m
import numpy as np
import torch

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "ml" / "23-training-infrastructure"
STEPS, REPS = 100, 5


def one(fmt, vec=False):
    torch.set_num_threads(1)
    model = m.fresh(0)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    mu, sd = m.scale()
    loads, batches, computes = [], [], []
    for _ in range(REPS):
        t0 = time.perf_counter()
        sh = m.shards(fmt)
        loads.append(time.perf_counter() - t0)
        smp = m.WindowSampler(sh.lengths, m.T, m.H, 256, seed=0)
        tb = tc = 0.0
        for _ in range(STEPS):
            t0 = time.perf_counter()
            X, y = (m.make_batch_vec if vec else m.make_batch)(sh, *smp.next(), m.T, m.H, 0)
            X = (X - mu) / sd
            t1 = time.perf_counter()
            opt.zero_grad()
            ((model(X)[:, 0] - y) ** 2).mean().backward()
            opt.step()
            t2 = time.perf_counter()
            tb, tc = tb + t1 - t0, tc + t2 - t1
        batches.append(tb / STEPS)
        computes.append(tc / STEPS)
    load, batch, comp = np.median(loads), np.median(batches), np.median(computes)
    data = load / STEPS + batch
    return load * 1e3, batch * 1e3, comp * 1e3, data / (data + comp)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "measured_loader.csv", "w") as f:
        f.write("i,format,load_ms,load_mb_s,batch_ms,compute_ms,data_share\n")
        size = m.sizes()
        for i, (fmt, vec) in enumerate((("csv", False), ("npy", False), ("mmap", False), ("mmap", True))):
            load, batch, comp, share = one(fmt, vec)
            name = fmt + ("-gather" if vec else "")
            f.write(f"{i},{name},{load:.2f},{size[fmt] / 1e6 / (load / 1e3):.0f},{batch:.3f},{comp:.3f},{share:.3f}\n")
    cpu = next(ln.split(":", 1)[1].strip() for ln in open("/proc/cpuinfo") if ln.startswith("model name"))
    meta = {"cpu": cpu, "logical_cpus": os.cpu_count(), "kernel": platform.release(),
            "python": platform.python_version(),
            "torch": torch.__version__, "numpy": np.__version__, "torch_threads": 1,
            "loadavg_1_5_15": " ".join(f"{x:.2f}" for x in os.getloadavg()),
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "nice": os.nice(0), "isolated_cores": "none",
            "shared": "yes: other jobs may have run on the machine",
            "source": "code/ml/23-training-infrastructure/python/bench_train.py"}
    (OUT / "measured_loader.csv.meta").write_text("".join(f"{k}: {v}\n" for k, v in meta.items()))


if __name__ == "__main__":
    main()
