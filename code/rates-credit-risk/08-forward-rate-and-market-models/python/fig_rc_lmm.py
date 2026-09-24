"""Chart data for Book 6, chapter 8 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rc_lmm import abcd_curve, caplet_check, correlation_rows, swaption_table  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "abcd.csv", "w") as f:
    f.write("tau,g\n")
    for t, g in abcd_curve():
        f.write(f"{t:.2f},{g:.5f}\n")
with open(OUT / "corr.csv", "w") as f:
    f.write("j,b02,b10,b40\n")
    for row in correlation_rows():
        f.write(",".join(f"{x:.4f}" for x in row) + "\n")
with open(OUT / "caplets.csv", "w") as f:
    f.write("k,target,mc,err\n")
    for row in caplet_check():
        f.write(",".join(f"{x:.4f}" for x in row) + "\n")
with open(OUT / "swaptions.csv", "w") as f:
    f.write("tenor,reb02,mc02,reb40,mc40\n")
    for row in swaption_table():
        f.write(",".join(f"{x:.4f}" for x in row) + "\n")
