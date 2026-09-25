"""Chart data for Book 8, chapter 26 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_voltarget import seeds, spike  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "seeds.csv", "w") as f:
    f.write("constant,managed\n")
    for s, _ in seeds():
        f.write(f"{s[0]:.4f},{s[1]:.4f}\n")

o = spike(0.0)
with open(OUT / "spike.csv", "w") as f:
    f.write("day,exposure,flow_pct\n")
    for t in range(240, 300):
        f.write(f"{t - 250},{o['exp'][t]:.4f},{100 * o['flow'][t]:.3f}\n")
