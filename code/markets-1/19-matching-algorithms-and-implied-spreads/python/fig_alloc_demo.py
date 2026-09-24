"""Chart data for Chapter 19 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from alloc_demo import EXAMPLE, compare, expected_fill_by_position, fill_vs_size

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/19-matching-algorithms-and-implied-spreads"
OUT.mkdir(parents=True, exist_ok=True)

res = compare(EXAMPLE, 100)
with open(OUT / "alloc.csv", "w") as f:
    f.write("order,fifo,pro_rata,split\n")
    for o in EXAMPLE:
        f.write(f"{o.oid}," + ",".join(str(res[k].get(o.oid, 0)) for k in ("fifo", "pro_rata", "split")) + "\n")

with open(OUT / "oversize.csv", "w") as f:
    f.write("shown,filled\n")
    f.writelines(f"{s},{q}\n" for s, q in fill_vs_size(range(0, 401), 1000, 100))

ahead = np.arange(0, 491, 10)
fi, pr = expected_fill_by_position(ahead, 10, 500, 120.0, 40_000, 19)
with open(OUT / "position.csv", "w") as f:
    f.write("ahead,fifo,pro_rata\n")
    f.writelines(f"{a},{x:.3f},{y:.3f}\n" for a, x, y in zip(ahead, fi, pr, strict=True))
