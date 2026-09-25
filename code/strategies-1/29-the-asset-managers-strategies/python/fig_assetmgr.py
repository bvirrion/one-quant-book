"""Chart data for Book 8, chapter 29 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_assetmgr import SIZES, replicate, transition_plan  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "sampling.csv", "w") as f:
    f.write("names,te_pct,te_ex_pct\n")
    for n in SIZES:
        v = replicate(n)
        f.write(f"{n},{100 * v['te']:.3f},{100 * v['te_ex']:.3f}\n")

plan, _, _ = transition_plan()
with open(OUT / "transition.csv", "w") as f:
    f.write("days,cost_bp,risk_bp,total_bp\n")
    for d, (c, r) in plan.items():
        f.write(f"{d},{1e4 * c:.2f},{1e4 * r:.2f},{1e4 * (c + r):.2f}\n")
