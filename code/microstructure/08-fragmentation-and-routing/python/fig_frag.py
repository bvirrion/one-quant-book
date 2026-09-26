"""Chart data for Book 10, chapter 8 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_frag import study  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

r = study()
with open(OUT / "delay.csv", "w") as f:
    f.write("ms,share,linear\n")
    for d, x in r["delays"].items():
        f.write(f"{d},{100 * x:.6f},{100 * r['price_changes_per_s'] * d / 1000:.6f}\n")

with open(OUT / "shares.csv", "w") as f:
    f.write("k,low,high,mid,err,cs,low_close,high_close,mid_close,err_close\n")
    a, c = r["is"], r["is_close"]
    for k in range(3):
        f.write(f"{k},{a['is_low'][k]:.4f},{a['is_high'][k]:.4f},{a['is_mid'][k]:.4f},"
                f"{0.5 * (a['is_high'][k] - a['is_low'][k]):.4f},{a['component_share'][k]:.4f},{c['is_low'][k]:.4f},"
                f"{c['is_high'][k]:.4f},{c['is_mid'][k]:.4f},{0.5 * (c['is_high'][k] - c['is_low'][k]):.4f}\n")
