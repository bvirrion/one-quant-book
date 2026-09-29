"""Chart data for Book 16, chapter 10 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_pay as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "scatter.csv", "w") as f:
    f.write("sharpe,pay\n")
    for seed in range(13, 18):
        s, p = m.one_desk(seed)
        for a, b in zip(s, p, strict=True):
            f.write(f"{a:.3f},{b:.3f}\n")

sim, lin = m.corr_by_years()
with open(OUT / "corr.csv", "w") as f:
    f.write("years,simulated,linear\n")
    for t, (a, b) in enumerate(zip(sim, lin, strict=True), start=1):
        f.write(f"{t},{a:.3f},{b:.3f}\n")

plan = m.bp.DeferralPlan(0.6, 4)
with open(OUT / "vesting.csv", "w") as f:
    f.write("year,c0,c1,c2,c3,c4\n")
    for y in range(8):
        row = []
        for cohort in range(5):
            k = y - cohort
            s = m.bp.schedule(1.0, plan)
            row.append(s[k] if 0 <= k < len(s) else 0.0)
        f.write(f"{y}," + ",".join(f"{x:.2f}" for x in row) + "\n")
