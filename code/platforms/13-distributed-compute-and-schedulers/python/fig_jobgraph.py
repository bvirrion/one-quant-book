"""Chart data for One Quant Book 15, chapter 13 (deterministic given measured_backtests.csv: the simulated sweep's
spread is the measured one)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_jobgraph import caching, fair_share, measured_sigma, policies, profile  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

s = measured_sigma()
rows = policies(s)
with open(OUT / "makespans.csv", "w") as f:
    f.write("policy,plain,backups\n")
    for name, lab in (("FIFO", "FIFO"), ("LPT", "LPT"), ("work stealing", "work stealing")):
        m = {r["spec"]: r["makespan_h"] for r in rows if r["policy"] == name}
        f.write(f"{lab},{m[False]:.2f},{m[True]:.2f}\n")
with open(OUT / "policies.csv", "w") as f:
    f.write("policy,spec,makespan_h,node_hours,wasted_core_h,backups,bound_h\n")
    for r in rows:
        f.write(f"{r['policy']},{int(r['spec'])},{r['makespan_h']:.2f},{r['node_hours']:.1f},{r['wasted_core_h']:.1f},"
                f"{r['backups']},{r['bound_h']:.2f}\n")
for name, (g, b) in profile(s).items():
    with open(OUT / f"profile_{name.lower()}.csv", "w") as f:
        f.write("t_h,busy\n")
        for t, x in zip(g, b, strict=True):
            f.write(f"{t:.4f},{x}\n")
with open(OUT / "fairshare.csv", "w") as f:
    f.write("policy,team_b_half_h,team_b_done_h,team_a_done_h\n")
    for r in fair_share(s):
        f.write(f"{r['policy']},{r['team_b_half_h']:.2f},{r['team_b_done_h']:.2f},{r['team_a_done_h']:.2f}\n")
c = caching(s)
with open(OUT / "caching.csv", "w") as f:
    f.write("case,makespan_h,core_hours\n")
    for k, lab in (("inline", "features recomputed in every backtest"), ("graph", "task graph; features once"),
                   ("cached", "next sweep; features from the cache")):
        f.write(f"{lab},{c[k + '_h']:.2f},{c[k + '_core_h']:.0f}\n")
