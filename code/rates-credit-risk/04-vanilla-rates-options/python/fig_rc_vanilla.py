"""Chart data for Book 6, chapter 4 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rc_vanilla import cap_strike_table, smile_from_flat_normal, strip_table  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "smile.csv", "w") as f:
    f.write("k,black\n")
    for k, v in smile_from_flat_normal():
        f.write(f"{100 * k:.2f},{v:.3f}\n")

with open(OUT / "strip.csv", "w") as f:
    f.write("t,caplet,flat\n")
    for t, a, b in strip_table():
        f.write(f"{t:.3f},{a:.2f},{b:.2f}\n")

with open(OUT / "capstrike.csv", "w") as f:
    f.write("k,pct,bp\n")
    for k, p, b in cap_strike_table():
        f.write(f"{k:.2f},{p:.4f},{b:.3f}\n")
