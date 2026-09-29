"""Chart data for Book 16, chapter 14 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_treasury as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "margins.csv", "w") as f:
    f.write("pos,allocation,A,B,C\n")
    for i, (k, v) in enumerate(m.summary().items()):
        f.write(f"{i},{k}," + ",".join(f"{x:.3f}" for x in v["by_broker"]) + "\n")

one = m.allocations()["all at B"]
runs = {"base": m.run(False), "stress": m.run(True, 0), "lockup": m.run(True, 30), "one": m.run(True, 0, one)}
with open(OUT / "runway.csv", "w") as f:
    f.write("day," + ",".join(runs) + "\n")
    f.write("0," + ",".join(f"{m.CASH0:.3f}" for _ in runs) + "\n")
    for t in range(m.DAYS):
        f.write(f"{t + 1}," + ",".join(f"{r['cash'][t]:.3f}" for r in runs.values()) + "\n")

with open(OUT / "req.csv", "w") as f:
    _, r0 = m.paths(True, None, 0)
    _, r30 = m.paths(True, None, 30)
    f.write("day,nolock,lock\n")
    for t in range(m.DAYS):
        f.write(f"{t + 1},{r0[t].sum():.3f},{r30[t].sum():.3f}\n")
