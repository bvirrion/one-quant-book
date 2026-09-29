"""Chart data for Book 16, chapter 16 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_compliance as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

q50, q150 = m.queue(50), m.queue(150)
with open(OUT / "queue.csv", "w") as f:
    f.write("rate,h50,h150\n")
    for r in m.RATES:
        f.write(f"{100 * r:.2f},{q50['curve'][r]:.3f},{q150['curve'][r]:.3f}\n")

order = ["approved", "firm traded recently", "restricted list", "insider", "holding period", "watch list"]
rs = m.reasons()
with open(OUT / "reasons.csv", "w") as f:
    f.write("pos,reason,count\n")
    for i, k in enumerate(order):
        f.write(f"{i},{k},{rs.get(k, 0)}\n")
