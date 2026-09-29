"""Chart data for Book 17, chapter 13 (fixed seeds)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_pay as a  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

t = a.table()
with open(OUT / "dist.csv", "w") as f:
    f.write("pos,offer,p10,p25,p50,p75,p90,mean\n")
    for i, p in enumerate(a.OFFERS):
        s = t[p.name]
        vals = ",".join(f"{s[k] / 1000:.0f}" for k in ("p10", "p25", "p50", "p75", "p90", "mean"))
        f.write(f"{i + 1},{p.name},{vals}\n")

c = a.ce_curve()
with open(OUT / "ce_curve.csv", "w") as f:
    f.write("rra,bank,maker,platform\n")
    for j, r in enumerate(a.RRAS):
        vals = ",".join(f"{c[n][j] / 1000:.0f}" for n in ("bank", "market maker", "platform analyst"))
        f.write(f"{r},{vals}\n")

u, fo = a.bank_unvested(), a.forfeit_by_year()
with open(OUT / "bank_unvested.csv", "w") as f:
    f.write("year,unvested,forfeit\n")
    for y in range(a.YEARS):
        f.write(f"{y + 1},{u[y] / 1000:.0f},{fo[y] / 1000:.0f}\n")
