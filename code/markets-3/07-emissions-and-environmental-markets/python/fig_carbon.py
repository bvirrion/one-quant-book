"""Chart data for Book 3, Chapter 7 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_carbon import TNAC, spreads_curve, switching_curve

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/carbon"))
from firm_carbon import msr_intake

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "msr.csv", "w") as f:
    f.write("tnac,intake\n")
    for t in range(200, 1501, 1):
        f.write(f"{t},{msr_intake(t * 1_000_000) / 1e6:.1f}\n")
with open(OUT / "msrpoints.csv", "w") as f:
    f.write("tnac,intake\n")
    for t in TNAC.values():
        f.write(f"{t / 1e6:.1f},{msr_intake(t) / 1e6:.1f}\n")
with open(OUT / "switch.csv", "w") as f:
    f.write("gas,carbon\n")
    for g, c in switching_curve([10 + 2.5 * i for i in range(21)]):
        f.write(f"{g:.1f},{c:.2f}\n")
with open(OUT / "spreads.csv", "w") as f:
    f.write("carbon,spark,dark\n")
    for c, s, d in spreads_curve(100.0, [5 * i for i in range(31)]):
        f.write(f"{c},{s:.2f},{d:.2f}\n")
