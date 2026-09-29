"""Chart data for One Quant Book 15, chapter 14 (deterministic given measured_roof.csv: rooflines, the batch-size
curve of price requests)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_roofline import DEV, cpu_roof, request, roofline_grid  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

cpu = cpu_roof()
with open(OUT / "roofline.csv", "w") as f:
    f.write("intensity,cpu_gflops,device_gflops\n")
    for i, c, d in roofline_grid(cpu):
        f.write(f"{i:.5g},{c / 1e9:.5g},{d / 1e9:.5g}\n")
with open(OUT / "batch.csv", "w") as f:
    f.write("n,speedup,cpu_us,device_us\n")
    for n in np.unique(np.logspace(0, 6, 49).round().astype(int)):
        r = request(cpu, int(n))
        f.write(f"{n},{r['speedup']:.5g},{r['cpu_s'] * 1e6:.5g},{r['dev_s'] * 1e6:.5g}\n")
with open(OUT / "ridges.csv", "w") as f:
    f.write("roof,peak_gflops,bandwidth_gbs,ridge\n")
    f.write(f"one laptop core,{cpu.peak / 1e9:.2f},{cpu.bandwidth / 1e9:.2f},{cpu.ridge:.3f}\n")
    f.write(f"{DEV.name},{DEV.peak / 1e9:.0f},{DEV.bandwidth / 1e9:.0f},{DEV.ridge:.3f}\n")
