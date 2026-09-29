"""Chart data for One Quant Book 15, chapter 2 (deterministic: the simulated session and the storage model)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_tickcap import RETENTION_YEARS, economics, study  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

s = study()
with open(OUT / "layouts.csv", "w") as f:
    f.write("k,layout,bytes_per_msg\n")
    for k, (name, v) in enumerate(s["per_msg"].items()):
        f.write(f"{k},{name.replace(',', ';')},{v:.3f}\n")
eco = economics(s["per_msg"])
with open(OUT / "stored.csv", "w") as f:
    names = list(eco)
    f.write("years," + ",".join(f"s{i}" for i in range(len(names))) + "\n")
    for y in range(RETENTION_YEARS + 1):
        f.write(f"{y}," + ",".join(f"{eco[n]['PB_year'] * y:.4f}" for n in names) + "\n")
