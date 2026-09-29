"""Measure the kernel's receive path on this laptop (loopback UDP; no bypass hardware): three read methods, and
the split at the kernel's software receive timestamp. Writes figdata/.../measured_rx.csv and measured_rx_q.csv
with a .meta sidecar. Not run by `make figdata`: measured data, like Book 13's."""
import pathlib
import platform
import subprocess
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
OUT = ROOT / "figdata" / "networks" / "03-network-cards-and-kernel-bypass"
MODES = {0: "blocking", 1: "busy polling", 2: "batched (recvmmsg)"}
QUANT = (0.5, 0.9, 0.99, 0.999)


def run(n=20000, gap_ns=20000):
    exe = HERE / "cpp" / "bin" / "nw_rx_bench"
    exe.parent.mkdir(exist_ok=True)
    subprocess.run(["g++", "-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror", str(HERE / "cpp" / "nw_rx_bench.cpp"),
                    "-o", str(exe)], check=True)
    txt = subprocess.run([str(exe), str(n), str(gap_ns)], check=True, capture_output=True, text=True).stdout
    return np.genfromtxt(txt.splitlines(), delimiter=",", names=True, dtype=np.int64)


def summarise(a):
    rows = []
    for m in MODES:
        x = a[a["mode"] == m]
        parts = {"to kernel": x["kernel_ns"] - x["sent_ns"], "kernel to application": x["app_ns"] - x["kernel_ns"],
                 "total": x["app_ns"] - x["sent_ns"]}
        for k, v in parts.items():
            rows.append((m, k, *[float(np.quantile(v, q)) for q in QUANT]))
    return rows


def main():
    a = run(*(int(x) for x in sys.argv[1:3]))
    OUT.mkdir(parents=True, exist_ok=True)
    lines = ["mode,stage,p50_ns,p90_ns,p99_ns,p999_ns"]
    lines += [f"{m},{k.replace(' ', '_')},{a1:.0f},{a2:.0f},{a3:.0f},{a4:.0f}" for m, k, a1, a2, a3, a4 in summarise(a)]
    (OUT / "measured_rx.csv").write_text("\n".join(lines) + "\n")
    q = np.array([0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 0.995, 0.999])
    lines = ["q,blocking,busy,batched"]
    tot = {m: (a[a["mode"] == m]["app_ns"] - a[a["mode"] == m]["sent_ns"]) / 1000 for m in MODES}
    for qq in q:
        lines.append(f"{qq},{np.quantile(tot[0], qq):.2f},{np.quantile(tot[1], qq):.2f},{np.quantile(tot[2], qq):.2f}")
    (OUT / "measured_rx_q.csv").write_text("\n".join(lines) + "\n")
    meta = (f"machine: Intel Core Ultra 7 155H laptop, WSL2 ({platform.release()}), no isolated cores\n"
            f"compiler: g++ -std=c++20 -O2; loopback UDP, 64-byte datagrams, {len(a) // 3} per mode"
            " after 2000 warm-up\n")
    for n in ("measured_rx.csv", "measured_rx_q.csv"):
        (OUT / (n + ".meta")).write_text(meta)


if __name__ == "__main__":
    main()
