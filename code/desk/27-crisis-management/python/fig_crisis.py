"""Chart data for Book 16, chapter 27 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_crisis as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

b, n = m.baseline(), m.no_failure()
_, p = m.plan()
with open(OUT / "cash.csv", "w") as f:
    f.write("hour,baseline,plan,nofail,calls\n")
    for h in range(m.HOURS):
        f.write(f"{h},{b['cash'][h]:.3f},{p['cash'][h]:.3f},{n['cash'][h]:.3f},{b['calls'][h]:.3f}\n")

with open(OUT / "steps.csv", "w") as f:
    f.write("pos,action,horizon,cost\n")
    f.write(f"0,no action,{b['horizon']},0.000\n")
    for i, (a, h, c) in enumerate(m.steps(), start=1):
        f.write(f"{i},{a.replace('%', ' pct')},{h},{c:.3f}\n")
