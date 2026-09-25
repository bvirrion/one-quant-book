"""Chart data for Book 8, chapter 10 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_index import PRE, path_for_figure, trades  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

paths = {e: path_for_figure(0.15, e) for e in (0.2, 0.5, 0.8)}
with open(OUT / "path.csv", "w") as f:
    f.write("day,early02,early05,early08\n")
    for k in range(len(paths[0.5])):
        f.write(f"{k - PRE}," + ",".join(f"{100 * paths[e][k]:.4f}" for e in (0.2, 0.5, 0.8)) + "\n")

with open(OUT / "grid.csv", "w") as f:
    f.write("early,share5,share15,share30\n")
    for e in (0.2, 0.5, 0.8):
        f.write(f"{e}," + ",".join(f"{100 * trades(s, e)['announce']:.3f}" for s in (0.05, 0.15, 0.30)) + "\n")
