"""Chart data for Book 6, chapter 3 (deterministic)."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rc_ratesrisk import TENORS, balanced_book, components, hedge, treasury_changes  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

book, _ = balanced_book()
h = hedge(book)
with open(OUT / "ladder.csv", "w") as f:
    f.write("i,tenor,book,hedged\n")
    for i, (n, a, b) in enumerate(zip(TENORS, h["ladder"], h["hedged"], strict=True)):
        f.write(f"{i},{n}Y,{a / 1000:.3f},{round(b / 1000, 3) + 0.0:.3f}\n")

_, v, _ = components()
with open(OUT / "pca.csv", "w") as f:
    f.write("m,pc1,pc2,pc3\n")
    for n, row in zip(TENORS, v[:, :3], strict=True):
        f.write(f"{n}," + ",".join(f"{x:.4f}" for x in row) + "\n")

dates, ch = treasury_changes(start="2024-09-01")
with open(OUT / "pnl.csv", "w") as f:
    f.write("t,book,hedged\n")
    for d, row in zip(dates, ch, strict=True):
        y = dt.date.fromisoformat(d)
        t = y.year + (y.timetuple().tm_yday - 1) / 365.0
        f.write(f"{t:.4f},{row @ h['ladder'] / 1e6:.4f},{row @ h['hedged'] / 1e6:.4f}\n")
