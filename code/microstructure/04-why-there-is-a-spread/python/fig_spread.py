"""Chart data for Book 10, chapter 4 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_spread import gm_learning, pin_bias  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

g = gm_learning()
with open(OUT / "gm.csv", "w") as f:
    f.write("n,mu10,mu30,mu50\n")
    for n in range(0, 151, 2):
        f.write(f"{n},{g[0.1]['mean_spread'][n]:.4f},{g[0.3]['mean_spread'][n]:.4f},{g[0.5]['mean_spread'][n]:.4f}\n")

with open(OUT / "pin.csv", "w") as f:
    f.write("sd,none,none_sd,info,info_sd\n")
    for sd in (0.0, 0.25, 0.5, 0.75):
        a, b = pin_bias(sd, 0.0), pin_bias(sd, 0.4)
        f.write(f"{sd},{a['mean']:.4f},{a['sd']:.4f},{b['mean']:.4f},{b['sd']:.4f}\n")
