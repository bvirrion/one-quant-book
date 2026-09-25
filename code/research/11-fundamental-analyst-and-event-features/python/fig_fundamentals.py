"""Chart data for Book 7, chapter 11 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_fundamentals import apple_ttm, calendar_summary, ic_inflation  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

by = calendar_summary()["by_name"].sort_values(("release", "median"))
with open(OUT / "calendar.csv", "w") as f:
    f.write("k,name,release,filing\n")
    for k, (name, r) in enumerate(by.iterrows()):
        f.write(f"{k},{name},{r[('release', 'median')]:.1f},{r[('filing', 'median')]:.1f}\n")

first, latest = apple_ttm()
with open(OUT / "apple_ttm.csv", "w") as f:
    f.write("year,first,latest\n")
    for end in sorted(first):
        y, m, d = (int(x) for x in end.split("-"))
        f.write(f"{y + (m - 1 + d / 31) / 12:.3f},{first[end]:.4f},{latest[end]:.4f}\n")

ic = ic_inflation()
with open(OUT / "ic.csv", "w") as f:
    f.write("k,ic,se2\n")
    for k, name in enumerate(("sue_known", "sue_end", "bp_known_stale", "bp_end")):
        f.write(f"{k},{ic[name]:.4f},{2 * ic[name + '_se']:.4f}\n")
