"""Chart data for Book 8, chapter 3 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_residarb import YEAR, path, run, stability  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
PID = 7

with open(OUT / "path.csv", "w") as f:
    f.write("year,s,pos\n")
    for t, s, _, p in path(PID):
        f.write(f"{t / YEAR:.4f},{s:.4f},{p}\n")

with open(OUT / "sens_open.csv", "w") as f:
    f.write("s_open,sr_gross,sr_net\n")
    for so in (0.75, 1.0, 1.25, 1.5, 2.0):
        r = run(0.3, "etf", so)
        f.write(f"{so},{r['sr_gross']:.4f},{r['sr_net']:.4f}\n")

with open(OUT / "sens_kappa.csv", "w") as f:
    f.write("max_tau_days,passed_pct,sr_net\n")
    for tau in (5, 10, 15, 30):
        r = run(0.3, "etf", 1.25, YEAR / tau)
        f.write(f"{tau},{100 * r['passed']:.1f},{r['sr_net']:.4f}\n")

with open(OUT / "stability.csv", "w") as f:
    f.write("year,explained_pct,subspace,min_cos\n")
    for row in stability()[1:]:
        f.write(f"{row['t'] / YEAR:.3f},{100 * row['explained']:.2f},{row['subspace']:.4f},{row['min_cos']:.4f}\n")
