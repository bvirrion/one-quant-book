"""Chart data for Book 10, chapter 10 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_auction import GRID, TAUS, auction_study, close_session, race_study  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

a = auction_study()
with open(OUT / "gap.csv", "w") as f:
    f.write("s,gap,se\n")
    for g, x, e in zip(GRID, a["gap"], a["gap_se"], strict=True):
        f.write(f"{g},{x:.4f},{e:.4f}\n")
with open(OUT / "late.csv", "w") as f:
    f.write("tau,fixed,fixed_se,random,random_se\n")
    for tau in TAUS:
        fx, rd = a[(0.0, tau)], a[(30.0, tau)]
        f.write(f"{tau},{fx['impact']:.4f},{fx['impact_se']:.4f},{rd['impact']:.4f},{rd['impact_se']:.4f}\n")
r = close_session(1)
with open(OUT / "path.csv", "w") as f:
    f.write("s,price,paired\n")
    for row in r["ind"]:
        f.write(f"{(r['final'][0] - row['t']) / 1e9:.1f},{row['price'] / 10_000:.4f},{row['paired']}\n")
race = race_study()
with open(OUT / "race.csv", "w") as f:
    f.write("interval,gap150,gap1000\n")
    for iv in (1.0, 10.0, 100.0):
        f.write(f"{iv},{race[(iv, 200.0, 50.0)]:.4f},{race[(iv, 1050.0, 50.0)]:.4f}\n")
