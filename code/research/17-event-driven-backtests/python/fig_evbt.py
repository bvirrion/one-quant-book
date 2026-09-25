"""Chart data for Book 7, chapter 17 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_evbt import level1, run  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

cases = [("touch", 0.0, "conservative"), ("penetration", 0.0, "conservative"), ("capped", 0.0, "conservative"),
         ("touch", 5.0, "optimistic"), ("penetration", 5.0, "optimistic"), ("capped", 5.0, "optimistic")]
with open(OUT / "models.csv", "w") as f:
    f.write("k,lots,pnl,markout\n")
    for k, (m, lat, pol) in enumerate(cases):
        r = run(m, lat, pol)
        n = len(r)
        f.write(f"{k},{sum(d['filled_lots'] for d in r) / n:.2f},{sum(d['pnl'] for d in r) / n:.2f},"
                f"{sum(d['markout'] for d in r) / n:.4f}\n")
    lv = level1()
    f.write(f"6,0,{sum(lv) / len(lv):.2f},0\n")
