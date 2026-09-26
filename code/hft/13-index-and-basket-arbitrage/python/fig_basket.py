"""Chart data for Book 11, chapter 13 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hf_basket as h  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

slow, fast = h.sweep(20.0), h.sweep(2.0)
with open(OUT / "edge.csv", "w") as f:
    f.write("k,mean20,sharpe20,mean2,sharpe2,capture20,costs\n")
    for k in h.KS:
        f.write(f"{k},{slow[k]['mean']:.4f},{slow[k]['sharpe']:.4f},{fast[k]['mean']:.4f},{fast[k]['sharpe']:.4f},"
                f"{slow[k]['capture']:.4f},{slow[k]['costs']:.4f}\n")
