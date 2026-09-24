"""Chart data for Chapter 23 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from option_basics import EXP, example_book, shares_by_close

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/chain"))
from firm_chain import Series

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/23-option-contracts-and-exchanges"
OUT.mkdir(parents=True, exist_ok=True)

call, put = Series("XYZ", EXP, "C", 50_000), Series("XYZ", EXP, "P", 50_000)
with open(OUT / "payoffs.csv", "w") as f:
    f.write("s,long_call,short_call,long_put,short_put\n")
    for k in range(80, 121):
        s = k / 2.0
        f.write(f"{s:.1f},{call.payoff(s, 2.40, 1) / 100:.2f},{call.payoff(s, 2.40, -1) / 100:.2f},"
                f"{put.payoff(s, 1.90, 1) / 100:.2f},{put.payoff(s, 1.90, -1) / 100:.2f}\n")

closes = [k / 100.0 for k in range(4600, 5451, 5)]
with open(OUT / "expiry.csv", "w") as f:
    f.write("close,shares\n")
    f.writelines(f"{c:.2f},{n}\n" for c, n in zip(closes, shares_by_close(example_book(), closes), strict=True))
