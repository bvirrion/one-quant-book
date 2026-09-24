"""Chart data for Book 3, Chapter 27 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_betting import flb_book, methods, returns_by_odds

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "flb.csv", "w") as f:
    f.write("idx,ret,n\n")
    for i, (_, r, n) in enumerate(returns_by_odds(flb_book()), 1):
        f.write(f"{i},{100 * r:.2f},{n}\n")

with open(OUT / "methods.csv", "w") as f:
    f.write("idx,fav,mid,long\n")
    for i, v in enumerate(methods().values(), 1):
        f.write(f"{i}," + ",".join(f"{100 * x:.2f}" for x in v) + "\n")
