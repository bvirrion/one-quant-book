"""Chart data for Book 11, chapter 5 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from hf_queues import QS, fitted, sweep, values  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

e = fitted()
with open(OUT / "intensities.csv", "w") as f:
    f.write("q,L,C,M\n")
    for q in range(1, 26):
        f.write(f"{q},{e['L'][q]:.3f},{e['C'][q]:.3f},{e['M'][q]:.3f}\n")

v = values()
with open(OUT / "values.csv", "w") as f:
    f.write("same,back2,front2,back20,front20\n")
    for i, s in enumerate(QS):
        j2, j20 = QS.index(2), QS.index(20)
        f.write(f"{s},{v['back']['value'][i, j2]:.3f},{v['front']['value'][i, j2]:.3f},"
                f"{v['back']['value'][i, j20]:.3f},{v['front']['value'][i, j20]:.3f}\n")

with open(OUT / "sweep.csv", "w") as f:
    f.write("theta,shares,markout10,edge10\n")
    for th, r in sweep().items():
        f.write(f"{th},{r['shares']:.1f},{r['markout10']:.4f},{r['edge10']:.3f}\n")
