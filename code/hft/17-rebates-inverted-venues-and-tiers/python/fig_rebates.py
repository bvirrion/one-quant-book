"""Chart data for Book 11, chapter 17 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hf_rebates as h  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

b = h.by_queue()
with open(OUT / "queue.csv", "w") as f:
    f.write("queue,mt,inv\n")
    for q in b["maker-taker"]:
        f.write(f"{q / 1000:g},{b['maker-taker'][q]:.4f},{b['inverted'][q]:.4f}\n")

with open(OUT / "chase.csv", "w") as f:
    f.write("natural,gain,cost,net\n")
    for r in h.chase_curve():
        f.write(f"{r['natural']},{r['gain'] / 1000:.1f},{r['cost'] / 1000:.1f},{r['net'] / 1000:.1f}\n")
