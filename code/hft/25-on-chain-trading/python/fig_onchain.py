"""Chart data for Book 11, chapter 25 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hf_onchain as h  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "auction.csv", "w") as f:
    f.write("n,share,searcher\n")
    for n, a in h.auctions().items():
        f.write(f"{n},{100 * a['share']:.2f},{a['searcher']:.3f}\n")

with open(OUT / "lp.csv", "w") as f:
    f.write("fee,fees,lvr,net\n")
    for fee, r in h.by_fee().items():
        f.write(f"{1e4 * fee:g},{r['fees'] / 1000:.2f},{r['lvr'] / 1000:.2f},{r['hedged_pnl'] / 1000:.2f}\n")
