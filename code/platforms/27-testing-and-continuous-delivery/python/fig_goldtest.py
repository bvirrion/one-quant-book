"""Chart data for One Quant Book 15, chapter 27 (deterministic: portfolio seed 27, MC seeds 1-40 and 100-107)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_goldtest import KS, eight_servers, expected_cost, experiment, noise_theory, rates, trains  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

ex = experiment()
with open(OUT / "tolerance.csv", "w") as f:
    f.write("k,asian_fix,day_count_asian,day_count_all,put_sign,finer_grid,noise_instrument,noise_theory,noise_run,cost\n")
    for k in KS:
        r = rates(ex, k)
        f.write(f"{k:g},{r['Asian fixing'][0] / r['Asian fixing'][1]:.2f},"
                f"{r['day_count_asian'][0] / r['day_count_asian'][1]:.2f},{r['day count'][0]}/{r['day count'][1]},"
                f"{r['put sign'][0]}/{r['put sign'][1]},{r['finer grid'][0]}/{r['finer grid'][1]},"
                f"{r['noise_instrument']:.4f},{noise_theory(k):.4f},{r['noise_run']:.3f},{expected_cost(ex, k):.0f}\n")
with open(OUT / "pinned.csv", "w") as f:
    r = rates(ex, 3.0, pinned=True)
    f.write("asian_fix,day_count_asian,day_count_all,noise_run\n")
    f.write(f"{r['Asian fixing'][0]}/{r['Asian fixing'][1]},{r['day_count_asian'][0]}/{r['day_count_asian'][1]},"
            f"{r['day count'][0]}/{r['day count'][1]},{r['noise_run']:.3f}\n")
with open(OUT / "errors.csv", "w") as f:
    f.write("product,mean_value,mean_error_unit,n\n")
    for g in ("european", "american", "asian", "barrier"):
        ks = [k for k in ex["base"] if k.startswith(g)]
        f.write(f"{g},{sum(ex['base'][k] for k in ks) / len(ks):.4f},{sum(ex['errs'][k] for k in ks) / len(ks):.3g},"
                f"{len(ks)}\n")
with open(OUT / "trains.csv", "w") as f:
    f.write("cadence_days,changes,mean_lead_days,mean_batch,bisect_steps\n")
    for c, n, lead, batch, steps in trains():
        f.write(f"{c},{n},{lead:.2f},{batch:.2f},{steps:.2f}\n")
with open(OUT / "servers.csv", "w") as f:
    e = eight_servers()
    f.write("host,build_hash,config_hash,matches_release\n")
    for h, (b, c) in sorted(e["hosts"].items()):
        f.write(f"{h},{b},{c},{h not in e['refused']}\n")
