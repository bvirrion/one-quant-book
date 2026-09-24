"""Chart data for Book 3, Chapter 4 (deterministic, from data/markets-3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_lng import history, load_gas

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)


def t(m: str) -> float:
    return int(m[:4]) + (int(m[5:]) - 0.5) / 12


with open(OUT / "hubs.csv", "w") as f:
    f.write("t,hh,eu,jp\n")
    for r in load_gas():
        f.write(f"{t(r['month']):.4f},{r['hh']:.3f},{r['eu']:.3f},{r['jp']:.3f}\n")
with open(OUT / "netback.csv", "w") as f:
    f.write("t,netback,fobvar\n")
    for c in history():
        f.write(f"{t(c['month']):.4f},{c['netback']:.3f},{c['fob']:.3f}\n")
