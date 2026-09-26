"""Chart data for Book 12, chapter 3 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ml_validation import selection  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/ml" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

s = selection()
with open(OUT / "seeds.csv", "w") as f:
    f.write("selection,fresh\n")
    for a, b in zip(s["scores"], s["fresh_scores"], strict=True):
        f.write(f"{100 * a:.4f},{100 * b:.4f}\n")
