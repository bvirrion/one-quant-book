"""Chart data for Book 16, chapter 8 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_drawdown as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

ea, pa, eb, pb = m.examples()
with open(OUT / "examples.csv", "w") as f:
    f.write("year,eq_alive,post_alive,eq_broken,post_broken\n")
    for t in range(0, len(ea), 5):
        f.write(f"{t / 252:.3f},{100 * ea[t]:.2f},{pa[t]:.3f},{100 * eb[t]:.2f},{pb[t]:.3f}\n")

tab = m.table()
with open(OUT / "rules.csv", "w") as f:
    f.write("k,rule,false,delay_years,value_alive,value_dead,value_mix\n")
    un = next(iter(tab.values()))
    f.write(f"0,none,0.0,nan,{100 * un['value_alive_unmanaged']:.1f},{100 * un['value_dead_unmanaged']:.1f},"
            f"{50 * (un['value_alive_unmanaged'] + un['value_dead_unmanaged']):.1f}\n")
    for k, (name, v) in enumerate(tab.items(), start=1):
        mix = 50 * (v["value_alive"] + v["value_dead"])
        f.write(f"{k},{name.replace('%', ' pct')},{v['false_per_100y']:.2f},{v['median_delay_days'] / 252:.2f},"
                f"{100 * v['value_alive']:.1f},{100 * v['value_dead']:.1f},{mix:.1f}\n")

with open(OUT / "lorden.csv", "w") as f:
    f.write("sr_dead,years\n")
    for s in np.round(np.arange(-2.0, 0.51, 0.1), 2):
        f.write(f"{s:.1f},{m.lorden(10.0, s):.2f}\n")
