"""Chart data for Book 11, chapter 18 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hf_news as h  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "reentry.csv", "w") as f:
    f.write("t,value\n")
    for t, v in h.reentry_curve().items():
        f.write(f"{t:g},{v:.2f}\n")
