"""Chart data for Book 7, chapter 23 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_markout import HORIZONS, curves, decomposition, tca_all  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

c = curves(False)
with open(OUT / "markout.csv", "w") as f:
    f.write("h,all,micro,informed,uninformed,all_lo,all_hi\n")
    for i, h in enumerate(HORIZONS):
        m, s = c["all"][0][i], c["all"][1][i]
        f.write(f"{max(h, 0.05):.2f},{m:.4f},{c['all_micro'][0][i]:.4f},{c['informed'][0][i]:.4f},"
                f"{c['uninformed'][0][i]:.4f},{m - 2 * s:.4f},{m + 2 * s:.4f}\n")

with open(OUT / "decomp.csv", "w") as f:
    f.write("part,plain,pull\n")
    a, b = decomposition(False, 20.0)[0], decomposition(True, 20.0)[0]
    for k in ("spread", "adverse", "inventory", "fees", "total"):
        f.write(f"{k},{a[k]:.1f},{b[k]:.1f}\n")

rows, _, _ = tca_all()
with open(OUT / "tca.csv", "w") as f:
    f.write("move_without,execution,total,paid\n")
    for r in rows:
        f.write(f"{r['move_without']:.2f},{r['execution']:.3f},{r['total']:.3f},{r['paid']:.3f}\n")
