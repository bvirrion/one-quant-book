"""Chart data for Book 17, chapter 5 (deterministic: fixed seeds; the ADV panel is committed)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_platforms as p  # noqa: E402

tt = p.tt

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

grid = np.arange(0, p.YEARS + 1e-9, 0.25)
cols = [("tight", p.TIGHT, 0.5), ("tight", p.TIGHT, 1.0), ("loose", p.LOOSE, 0.5), ("loose", p.LOOSE, 1.0)]
curves = [tt.survival(p.times(sr, lad), grid) for _, lad, sr in cols]
with open(OUT / "survival.csv", "w") as f:
    f.write("years,tight05,tight10,loose05,loose10\n")
    for i, g in enumerate(grid):
        f.write(f"{g:.2f}," + ",".join(f"{c[i]:.4f}" for c in curves) + "\n")

names = {"Millennium Management": "mlp", "Balyasny Asset Management": "bam", "Schonfeld Strategic Advisors": "sch",
         "ExodusPoint Capital Management": "exo"}
for plat, short in names.items():
    with open(OUT / f"adv_{short}.csv", "w") as f:
        f.write("t,employees\n")
        for r in p.panel():
            if r["platform"] == plat:
                y, m = r["file"].split("-")
                f.write(f"{int(y) + (int(m) - 1) / 12:.3f},{r['employees'] / 1000:.3f}\n")
