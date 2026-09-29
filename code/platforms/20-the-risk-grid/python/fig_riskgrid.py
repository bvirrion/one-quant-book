"""Chart data for One Quant Book 15, chapter 20 (deterministic given measured_costs.csv)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_riskgrid import failure_policies, sweep  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

rows = sweep()
for cores in (32, 64):
    with open(OUT / f"sweep_{cores}.csv", "w") as f:
        f.write("scen_batch,naive_h,aware_h,tasks,naive_s,aware_s\n")
        by = {(r["scen_batch"], r["cost_aware"]): r for r in rows if r["cores"] == cores}
        for b in sorted({r["scen_batch"] for r in rows}):
            f.write(f"{b},{by[(b, False)]['makespan'] / 3600:.4f},{by[(b, True)]['makespan'] / 3600:.4f},"
                    f"{by[(b, False)]['tasks']},{by[(b, False)]['makespan']:.0f},{by[(b, True)]['makespan']:.0f}\n")
with open(OUT / "failures.csv", "w") as f:
    f.write("policy,makespan_s,wasted_s,lost_cells\n")
    for pol, r in failure_policies().items():
        f.write(f"{pol},{r['makespan']:.0f},{r['wasted']:.0f},{r['lost']}\n")
