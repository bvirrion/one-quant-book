"""Chart data for Book 6, chapter 2 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rc_multicurve import collateral_table, forward_table, switch_table  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "forwards.csv", "w") as f:
    f.write("t,euribor,ois,basis\n")
    for t, a, b, c in forward_table(0.25):
        f.write(f"{t:.2f},{a:.4f},{b:.4f},{c:.3f}\n")

with open(OUT / "collateral.csv", "w") as f:
    f.write("t,usd,eur,eff\n")
    for t, a, b, c in collateral_table(0.1):
        f.write(f"{t:.1f},{a:.4f},{b:.4f},{c:.4f}\n")

with open(OUT / "switch.csv", "w") as f:
    f.write("i,years,pv,change\n")
    for i, (n, pv, ch) in enumerate(switch_table()):
        f.write(f"{i},{n}y,{pv:.3f},{ch:.2f}\n")
