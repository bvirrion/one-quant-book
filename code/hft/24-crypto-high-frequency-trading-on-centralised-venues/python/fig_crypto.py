"""Chart data for Book 11, chapter 24 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hf_crypto as h  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "budget.csv", "w") as f:
    f.write("rate,total,adverse\n")
    for r, o in h.budget().items():
        f.write(f"{r:g},{o['total'] / 1000:.2f},{o['adverse'] / 1000:.2f}\n")

w = h.week()
t0 = w.t0
res = h.ch.run(w, **(h.BASE | {"record": (t0 - 120, t0 + 3600)}))
pull = h.ch.run(w, **(h.BASE | {"absorb": False, "record": (t0 - 120, t0 + 3600)}))
with open(OUT / "cascade.csv", "w") as f:
    f.write("minute,basis,absorb,pull\n")
    for (t, b, pos), (_, _, pos2) in zip(res["path"][::20], pull["path"][::20], strict=True):
        f.write(f"{(t - t0) / 60:.2f},{1e4 * b:.2f},{pos / 1e6:.3f},{pos2 / 1e6:.3f}\n")
