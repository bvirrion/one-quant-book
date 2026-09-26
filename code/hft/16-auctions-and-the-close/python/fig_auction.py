"""Chart data for Book 11, chapter 16 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hf_auction as h  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

o = h.offers()
with open(OUT / "provider.csv", "w") as f:
    f.write("imbalance,move,ps0,ps15,ps50,close15\n")
    for i, mv in h.impact().items():
        c = h.am.close_price(h.BOOK, i, o[(i, 0.15)]["q"], o[(i, 0.15)]["k"])[0] - h.BOOK.p0
        f.write(f"{i / 1000:g},{mv},{o[(i, 0.0)]['per_share']:.3f},{o[(i, 0.15)]['per_share']:.3f},"
                f"{o[(i, 0.5)]['per_share']:.3f},{c}\n")
