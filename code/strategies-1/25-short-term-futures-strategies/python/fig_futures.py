"""Chart data for Book 8, chapter 25 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_futures import announcement_path, fade_table  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

paths, k = announcement_path()
with open(OUT / "announcement.csv", "w") as f:
    f.write("minute,before,after\n")
    for i in range(0, len(paths["before"]), 3):
        f.write(f"{i},{paths['before'][i]:.2f},{paths['after'][i]:.2f}\n")

with open(OUT / "fade.csv", "w") as f:
    f.write("z,gross,net\n")
    for z, (g, n) in fade_table().items():
        f.write(f"{z},{g:.3f},{n:.3f}\n")
