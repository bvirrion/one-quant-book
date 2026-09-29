"""Chart data for One Quant Book 15, chapter 21 (deterministic: the block on firm.exchsim and the week, seed 21)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_tradecap import allocations, block_fills, downstream, week  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

f = block_fills()
with open(OUT / "block.csv", "w") as out:
    out.write("fill,qty,price,seconds\n")
    for i, (q, p, ts) in enumerate(f):
        out.write(f"{i + 1},{q},{p / 1e4:.4f},{ts / 1e9 - 34_200:.3f}\n")
with open(OUT / "allocation.csv", "w") as out:
    out.write("rule,fund_a,fund_b,fund_c,allocated,residual,max_dev\n")
    for rule, r in allocations(f).items():
        a = r["alloc"]
        out.write(f"{rule},{a['fund A']},{a['fund B']},{a['fund C']},{r['allocated']},{r['residual']},"
                  f"{r['max_dev']:.0f}\n")
st, ev = week()
d = downstream(st, ev)
with open(OUT / "downstream.csv", "w") as out:
    out.write("system,copy_wrong,events_wrong\n")
    for name, w in d["wrong"].items():
        out.write(f"{name},{w},0\n")
    out.write(f"any disagreement,{d['disagree']},0\n")
