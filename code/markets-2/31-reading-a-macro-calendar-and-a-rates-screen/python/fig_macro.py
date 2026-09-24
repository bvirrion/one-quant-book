"""Chart data for Book 2, Chapter 31 (from H.15 data and seeded synthetic data)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from macro_demo import curve_rows, event_stats, payroll_moves

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
st = event_stats()
with open(OUT / "eventmoves.csv", "w") as f:
    f.write("k,series,payroll,other\n")
    series = (("2-year", "on2", "off2"), ("10-year", "on10", "off10"), ("2s10s", "on_s", "off_s"))
    for k, (name, a, b) in enumerate(series):
        f.write(f"{k},{name},{st[a]:.4f},{st[b]:.4f}\n")
with open(OUT / "payrollmoves.csv", "w") as f:
    f.write("date,d2,d10,kind\n")
    for d, d2, d10, kind in payroll_moves():
        f.write(f"{d},{d2:.1f},{d10:.1f},{kind.replace(' ', '-')}\n")
rows = {r["date"]: r for r in curve_rows()}
with open(OUT / "curves.csv", "w") as f:
    f.write("tenor," + ",".join(f"d{d.replace('-', '')}" for d in ("2025-09-22", "2026-03-23", "2026-09-22")) + "\n")
    for t in (2, 5, 10, 30):
        f.write(f"{t}," + ",".join(rows[d][f"y{t}"] for d in ("2025-09-22", "2026-03-23", "2026-09-22")) + "\n")
