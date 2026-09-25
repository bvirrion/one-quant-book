"""Chart data for Book 7, chapter 10 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_leadlag import LAGS, ccf, event_study, lead_recovery, size_table  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

t = size_table()
w = t[(t.weighting == "EW") & (t.freq == "weekly")]
with open(OUT / "size.csv", "w") as f:
    f.write("k,period,small_on_big,big_on_small,own_small\n")
    for k, r in enumerate(w.itertuples()):
        f.write(f"{k},{r.start}-{r.end},{r.small_on_big:.4f},{r.big_on_small:.4f},{r.own_small:.4f}\n")

win, ev = event_study()
with open(OUT / "event.csv", "w") as f:
    f.write("day,customer_tenth,supplier\n")
    for d, c, s in zip(win, ev["customer"], ev["supplier"], strict=True):
        f.write(f"{d},{100 * c / 10:.4f},{100 * s:.4f}\n")

fast, slow = ccf(0.5), ccf(0.5, 0.12)
with open(OUT / "ccf.csv", "w") as f:
    f.write("lag,fast,slow\n")
    for x, a, b in zip(LAGS, fast["ccf"], slow["ccf"], strict=True):
        f.write(f"{x:.2f},{a:.4f},{b:.4f}\n")

rec = lead_recovery()
with open(OUT / "recovery.csv", "w") as f:
    f.write("planted,fast,slow\n")
    for L in rec[1.0]:
        for (_, a), (_, b) in zip(rec[1.0][L], rec[0.12][L], strict=True):
            f.write(f"{L:.2f},{a:.2f},{b:.2f}\n")
