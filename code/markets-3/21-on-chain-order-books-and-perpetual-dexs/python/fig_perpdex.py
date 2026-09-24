"""Chart data for Book 3, Chapter 21 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_perpdex import BUFFER_3X, replay, squeeze_loss

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

a, c = replay("arrival"), replay("cancels_first")
with open(OUT / "pickoff.csv", "w") as f:
    f.write("block,arrival,cancels_first\n")
    for (b, _, la), (_, _, lc) in zip(a, c, strict=True):
        if b % 10 == 0:
            f.write(f"{b},{la:.0f},{lc:.0f}\n")

with open(OUT / "squeeze.csv", "w") as f:
    f.write("squeeze_pct,nocap,cap2,cap1\n")
    for k in range(0, 51):
        s = k / 10
        losses = ",".join(f"{squeeze_loss(n, s, BUFFER_3X) / 1e6:.3f}" for n in (10e6, 2e6, 1e6))
        f.write(f"{100 * s:.0f},{losses}\n")
