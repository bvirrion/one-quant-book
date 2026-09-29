"""Chart data for Book 17, chapter 8 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_owners as o  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

n = o.nbim()
with open(OUT / "costs.csv", "w") as f:
    f.write("k,label,bp\n")
    f.write(f"0,NBIM internal,{round(n['internal_bp'], 1)}\n1,NBIM whole fund,{n['total_bp']:.1f}\n")
    c = o.cpp()
    f.write(f"2,CPP operating,{round(c['operating_bp'], 1)}\n3,NBIM external mandates,{n['external_bp']:.1f}\n")
    f.write(f"4,CPP whole fund,{c['total_bp']:.1f}\n")

with open(OUT / "breakeven.csv", "w") as f:
    f.write("fee_bp,team5,team10,team20\n")
    for fee in range(5, 61, 5):
        b = [o.team_breakeven(h, fees=(fee,))[fee] / 1000 for h in (5, 10, 20)]
        f.write(f"{fee}," + ",".join(f"{x:.3f}" for x in b) + "\n")
