"""Chart data for Book 2, Chapter 14 (deterministic, from data/markets-2)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from fx_demo import load_bis

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-2/14-the-fx-market"
OUT.mkdir(parents=True, exist_ok=True)
rows = load_bis()

with open(OUT / "instruments.csv", "w") as f:
    f.write("k,label,y2022,y2025\n")
    for k, r in enumerate(x for x in rows if x["series"] == "instrument"):
        f.write(f"{k},{r['label']},{r['y2022']},{r['y2025']}\n")

with open(OUT / "currencies.csv", "w") as f:
    f.write("k,label,y2025\n")
    for k, r in enumerate(x for x in rows if x["series"] == "currency"):
        f.write(f"{k},{r['label']},{r['y2025']}\n")
