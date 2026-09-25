"""Chart data for Book 7, chapter 28 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_capacity import FRACTIONS, OVERLAPS, SIZES, curve, unwind  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

fx, op = curve("fixed"), curve("optimised")
with open(OUT / "capacity.csv", "w") as f:
    f.write("size,sr_fixed,sr_opt,profit_fixed,profit_opt\n")
    for k, s in enumerate(SIZES):
        f.write(f"{s:g},{max(fx['sr'][k], -2.0):.4f},{op['sr'][k]:.4f},{max(fx['profit'][k] / 1e6, -300):.2f},"
                f"{op['profit'][k] / 1e6:.2f}\n")

with open(OUT / "unwind_paths.csv", "w") as f:
    f.write("day," + ",".join(f"f{int(100 * x)}" for x in FRACTIONS) + "\n")
    paths = [unwind(1.0, x)["path"] for x in FRACTIONS]
    f.write("0," + ",".join("0" for _ in FRACTIONS) + "\n")
    for d in range(len(paths[0])):
        f.write(f"{d + 1}," + ",".join(f"{100 * p[d]:.4f}" for p in paths) + "\n")

with open(OUT / "unwind_grid.csv", "w") as f:
    f.write("fraction," + ",".join(f"o{int(100 * t)}" for t in OVERLAPS) + "\n")
    for x in FRACTIONS:
        f.write(f"{x:g}," + ",".join(f"{100 * unwind(t, x)['peak']:.4f}" for t in OVERLAPS) + "\n")
