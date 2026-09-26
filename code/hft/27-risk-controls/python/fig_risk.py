"""Chart data for Book 11, chapter 27 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hf_risk as h  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

SHORT = ["none", "person at 5 min", "throttle", "collar", "capital", "position", "loss limit", "all"]
with open(OUT / "controls.csv", "w") as f:
    f.write("i,label,loss\n")
    for i, (lab, r) in enumerate(zip(SHORT, h.table().values(), strict=True)):
        f.write(f"{i},{lab},{r['loss'] / 1e6:.3f}\n")

s = h.sweep()
for key in ("loss", "position"):
    with open(OUT / f"sweep_{key}.csv", "w") as f:
        f.write("threshold,loss,false\n")
        for v, (loss, fa) in s[key].items():
            f.write(f"{v / 1e6:g},{loss / 1e6:.3f},{100 * fa:.2f}\n")
