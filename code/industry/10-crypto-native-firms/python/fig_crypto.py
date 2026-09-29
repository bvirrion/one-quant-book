"""Chart data for Book 17, chapter 10 (deterministic: fixed seed)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_crypto as c  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "coinbase.csv", "w") as f:
    f.write("year,employees,revenue\n")
    for r in c.headcount():
        e = f"{r['employees'] / 1000:.3f}" if r["employees"] else "nan"
        f.write(f"{r['year']},{e},{r['revenue'] / 1000:.3f}\n")

edges, counts = c.grant_hist()
with open(OUT / "grant_hist.csv", "w") as f:
    f.write("mid,share\n")
    tot = counts.sum()
    for i, k in enumerate(counts):
        f.write(f"{(edges[i] + edges[i + 1]) / 2000:.1f},{100 * k / tot:.2f}\n")

with open(OUT / "perhead.csv", "w") as f:
    f.write("year,perhead\n")
    for y, v in c.per_head().items():
        f.write(f"{y},{v:.3f}\n")
