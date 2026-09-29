"""Chart data for Book 17, chapter 9 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_infra as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

rows = sorted(m.exchanges(), key=lambda r: -r["op_income_per_head_m"])
with open(OUT / "perhead.csv", "w") as f:
    f.write("k,firm,revenue,opincome\n")
    for k, r in enumerate(rows):
        f.write(f"{k},{r['firm']},{r['revenue_per_head_m']:.3f},{r['op_income_per_head_m']:.3f}\n")

with open(OUT / "skbands.csv", "w") as f:
    f.write("grade,lo,hi,mid,half\n")
    for g in range(9, 18):
        lo, hi = m.sec_band(g)
        f.write(f"{g},{lo / 1000:.2f},{hi / 1000:.2f},{(lo + hi) / 2000:.3f},{(hi - lo) / 2000:.3f}\n")

fl = m.filings()
LAB = {"all": "all titles", "software engineer": "software", "quant researcher": "research",
       "ml and data": "ML and data"}
with open(OUT / "filings.csv", "w") as f:
    f.write("pos,role," + ",".join(k.replace(" ", "_") for k in m.KINDS) + "\n")
    for i, role in enumerate(m.ROLES):
        vals = ",".join(f"{fl[(k, role)]['p50'] / 1000:.1f}" for k in m.KINDS)
        f.write(f"{i + 1},{LAB[role]},{vals}\n")
