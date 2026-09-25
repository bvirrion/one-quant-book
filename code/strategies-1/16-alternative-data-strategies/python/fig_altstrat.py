"""Chart data for Book 8, chapter 16 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_altstrat import PHIS, run  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "decay.csv", "w") as f:
    f.write("phi,sr_net,sr_head\n")
    for phi in PHIS:
        f.write(f"{phi},{run(phi)['sr_net']:.4f},{run(phi, 1)['sr_net']:.4f}\n")
