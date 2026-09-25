"""Chart data for Book 9, chapter 4 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_eventvol import by_error, hedging  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

e = by_error()
with open(OUT / "error.csv", "w") as f:
    f.write("quintile,err,mean\n")
    for i, (x, m) in enumerate(zip(e["err"], e["mean"], strict=True)):
        f.write(f"{i + 1},{x:.3f},{100 * m:.2f}\n")

for kind in ("clock", "band"):
    with open(OUT / f"scalping_{kind}.csv", "w") as f:
        f.write("rule,cost,sd\n")
        for name, v in hedging(False).items():
            if name != "never" and name.startswith("band") == (kind == "band"):
                f.write(f"{name},{100 * v['hedge_cost']:.2f},{100 * v['sd']:.2f}\n")
