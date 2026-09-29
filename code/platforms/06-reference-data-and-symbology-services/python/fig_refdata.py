"""Chart data for One Quant Book 15, chapter 6 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_refdata import basket_backtest, build, universe  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

u = universe()
rd, _ = build(u)
b = basket_backtest(rd, u)
with open(OUT / "basket.csv", "w") as f:
    f.write("k,method,ret\n")
    rows = [("truth", b["truth"]), ("point in time", b["pit"]),
            ("today's mapping; adjusted", b["today_mapping_adjusted"]),
            ("right names; unadjusted", b["right_names_unadjusted"]), ("today's mapping; unadjusted", b["naive"])]
    for k, (name, v) in enumerate(rows):
        f.write(f"{k},{name},{100 * v:.3f}\n")

def code(pids, listing_of):
    """1 for the ticker's first holder, 2 for the listing that reused it, 0 for none."""
    return 0 if not pids else {56: 1, 100: 2}.get(listing_of[pids[0]], 3)


listing_of = {rd.pid(k): i for i, k in enumerate(u.isin)}
last = len(u.prices) - 1
today = code(rd.resolve("ticker", "T056", last, last), listing_of)
with open(OUT / "t056.csv", "w") as f:
    f.write("day,pit,today,vendor_b\n")
    for d in range(0, last + 1, 2):
        pit = code(rd.resolve("ticker", "T056", d, d), listing_of)
        vb = [p for p in listing_of if rd.value("B", p, "ticker", d, d) == "T056"]
        f.write(f"{d},{pit},{today},{code(vb, listing_of)}\n")
