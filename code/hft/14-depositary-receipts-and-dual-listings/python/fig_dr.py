"""Chart data for Book 11, chapter 14 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hf_dr as h  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

b = h.by_minute(15)
with open(OUT / "error.csv", "w") as f:
    f.write("minute,home,proxy\n")
    for i, (x, y) in enumerate(zip(b["home"], b["proxy"], strict=True)):
        f.write(f"{15 * i + 7.5:g},{x:.2f},{y:.2f}\n")
