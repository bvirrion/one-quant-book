"""Chart data for Book 17, chapter 11 (reads the committed filings snapshot)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_accounts as a  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

rows = a.quadrature()
with open(OUT / "quadrature_years.csv", "w") as f:
    f.write("fy,revenue,staff,profit\n")
    for r in rows:
        f.write(f"{r['fy']},{r['revenue']:.1f},{r['staff']:.1f},{r['profit_after_tax']:.1f}\n")
with open(OUT / "quadrature_perhead.csv", "w") as f:
    f.write("fy,revenue_per_head,staff_per_head\n")
    for r in rows:
        f.write(f"{r['fy']},{r['revenue_per_head']:.2f},{r['staff_per_head']:.2f}\n")

js = a.jane_street()
with open(OUT / "jane_street_headcount.csv", "w") as f:
    f.write("year,group,llp\n")
    for y in range(2020, 2026):
        g = [r["employees"] for r in js if r["entity"] == a.G and r["year"] == y]
        p = [r["employees"] for r in js if r["entity"] == a.L and r["year"] == y]
        f.write(f"{y},{int(g[0]) if g else 0},{int(p[0]) if p else 0}\n")
