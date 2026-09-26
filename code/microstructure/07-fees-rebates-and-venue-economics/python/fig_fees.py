"""Chart data for Book 10, chapter 7 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_fees import by_awareness  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "venues.csv", "w") as f:
    f.write("aware,fill_mt,fill_inv,adverse_mt,adverse_inv,value_mt,value_inv,value_mt_se,value_inv_se\n")
    for a, r in by_awareness().items():
        m, i = r["MT"], r["INV"]
        f.write(f"{a},{m['fill_share']:.4f},{i['fill_share']:.4f},{m['adverse']:.4f},{i['adverse']:.4f},"
                f"{m['value']:.4f},{i['value']:.4f},{m['value_se']:.4f},{i['value_se']:.4f}\n")
