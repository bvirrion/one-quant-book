"""Chart data for One Quant Book 15, chapter 12 (deterministic: firm.tape sessions of one hour, seed 1 for the defects,
seeds 1-10 for the clean runs)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_parity import clean, defect_table  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

LABEL = {"wall_clock": "wall clock", "float_prices": "float prices", "arrival_order": "callback order",
         "acked_working": "ack semantics"}
rows = defect_table()
with open(OUT / "defects_sim.csv", "w") as f:
    f.write("defect,events,affected\n")
    for r in rows:
        if r["against"] == "sim":
            f.write(f"{LABEL[r['defect']]},{r['events']},{r['affected']}\n")
with open(OUT / "defects.csv", "w") as f:
    f.write("defect,against,first,events,seconds,affected,outputs\n")
    for r in rows:
        f.write(f"{LABEL[r['defect']]},{r['against']},{r['first']},{r['events']},{r['t']:.3f},{r['affected']},"
                f"{r['outputs']}\n")
with open(OUT / "clean.csv", "w") as f:
    f.write("seed,outputs,inputs,same_sim,same_replay\n")
    for r in clean():
        f.write(f"{r['seed']},{r['outputs']},{r['inputs']},{int(r['same_sim'])},{int(r['same_replay'])}\n")
