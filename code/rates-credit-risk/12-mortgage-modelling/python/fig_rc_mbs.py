"""Chart data for Book 6, chapter 12 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rc_mbs import base, io_po_table, price_rate_table, s_curve  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "scurve.csv", "w") as f:
    f.write("inc,cpr\n")
    for x, c in s_curve():
        f.write(f"{100 * x:.3f},{100 * c:.3f}\n")
b = base()
with open(OUT / "price.csv", "w") as f:
    f.write("shift,value,linear\n")
    for s, v in price_rate_table(b["oas"]):
        f.write(f"{s},{v:.4f},{100 * (1 - b['duration'] * s * 1e-4):.4f}\n")
with open(OUT / "iopo.csv", "w") as f:
    f.write("shift,io,po\n")
    for s, a, c in io_po_table(b["oas"]):
        f.write(f"{s},{a:.4f},{c:.4f}\n")

ROOT = pathlib.Path(__file__).resolve().parents[4]
with open(ROOT / "data/markets-2/fed_mbs_monthly.csv") as src, open(OUT / "fedmbs.csv", "w") as f:
    f.write("year,tn\n")
    for ln in list(src)[1:]:
        d, v = ln.strip().split(",")
        y = int(d[:4]) + (int(d[5:7]) - 1) / 12
        f.write(f"{y:.3f},{float(v) / 1000:.4f}\n")
