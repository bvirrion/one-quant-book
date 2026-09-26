"""Chart data for Book 10, chapter 15 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_beyond import AIMS, HALVES, STRENGTHS, aim_grid, signal_study  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

s = signal_study()
with open(OUT / "signal.csv", "w") as f:
    f.write("half," + ",".join(f"s{i},e{i}" for i in range(3)) + "\n")
    for h in HALVES:
        cells = [f"{s[(h, st)]['saved']:.3f},{s[(h, st)]['saved_se']:.3f}" for st in STRENGTHS]
        f.write(f"{h}," + ",".join(cells) + "\n")
g = aim_grid()
with open(OUT / "aim.csv", "w") as f:
    f.write("a,mean,sd,ce\n")
    st = g[AIMS[0]]
    f.write(f"0,{st['static'][0]:.3f},{st['static'][1]:.3f},{st['ce_static']:.3f}\n")
    for a in AIMS:
        f.write(f"{a},{g[a]['adaptive'][0]:.3f},{g[a]['adaptive'][1]:.3f},{g[a]['ce_adaptive']:.3f}\n")
