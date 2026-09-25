"""Chart data for Book 9, chapter 28 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_sphedge import BOOK, profile, table  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

p = profile()
with open(OUT / "profile.csv", "w") as f:
    f.write("spot,vega,hedge\n")
    for s, v, d in zip(p["spot"], p["vega"], p["delta"], strict=True):
        f.write(f"{100 * s:.0f},{v / 1e6:.3f},{-d / 0.01 / 1e6:.1f}\n")
t = table()
with open(OUT / "exposures.csv", "w") as f:
    f.write("k,exposure," + ",".join(f"n{i}" for i in range(len(BOOK))) + "\n")
    for k, (name, row) in enumerate(t.items()):
        f.write(f"{k},{name}," + ",".join(f"{row['by_note'].get(n.name, 0.0) / 1e6:.3f}" for n in BOOK) + "\n")
