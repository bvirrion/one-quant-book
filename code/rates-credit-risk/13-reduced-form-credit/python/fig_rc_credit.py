"""Chart data for Book 6, chapter 13 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rc_credit import TENORS, curve, hazard_table, upfront_table  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

c = curve()
with open(OUT / "hazard.csv", "w") as f:
    f.write("t,hazard,triangle\n")
    prev = 0.0
    for (T, h, tri, _pd) in hazard_table():
        f.write(f"{prev:.2f},{h:.4f},{tri:.4f}\n")
        prev = T
    f.write(f"{TENORS[-1]:.2f},{hazard_table()[-1][1]:.4f},{hazard_table()[-1][2]:.4f}\n")
with open(OUT / "survival.csv", "w") as f:
    f.write("t,q,pd\n")
    for i in range(0, 101):
        t = i / 10
        q = c.survival(t)
        f.write(f"{t:.1f},{100 * q:.4f},{100 * (1 - q):.4f}\n")
with open(OUT / "upfront.csv", "w") as f:
    f.write("s,u100,u500\n")
    for s, a, b in upfront_table():
        f.write(f"{s:.0f},{a:.4f},{b:.4f}\n")
