"""Chart data for One Quant Book 15, chapter 17 (deterministic: ten one-hour sessions, seeds 1-10, on firm.exchsim)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_posservice import at_close, timeline  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

rows = at_close()
keys = ["seed", "drop_min", "fills", "lost", "pending_s", "true_pos", "true_pnl", "session_pos_err", "session_pnl_err",
        "merged_pos_err", "merged_pnl_err", "merged+bust_pos_err", "merged+bust_pnl_err"]
with open(OUT / "at_close.csv", "w") as f:
    f.write(",".join(k.replace("+", "_") for k in keys) + "\n")
    for r in rows:
        f.write(",".join(f"{r[k]:.1f}" if isinstance(r[k], float) else str(r[k]) for k in keys) + "\n")
with open(OUT / "summary.csv", "w") as f:
    f.write("service,mean_abs_pos,mean_abs_pnl\n")
    labels = (("session", "session only"), ("merged", "with drop copy"), ("merged+bust", "with drop copy and bust"))
    for k, lab in labels:
        pos = np.mean([abs(r[f"{k}_pos_err"]) for r in rows])
        pnl = np.mean([abs(r[f"{k}_pnl_err"]) for r in rows])
        f.write(f"{lab},{pos:.0f},{pnl:.1f}\n")
t = timeline(3)
with open(OUT / "timeline.csv", "w") as f:
    f.write("t_min,session,merged,merged_bust,truth\n")
    for i in range(len(t["t_min"])):
        f.write(f"{t['t_min'][i]:.3f},{t['session'][i]},{t['merged'][i]},{t['merged+bust'][i]},{t['truth'][i]}\n")
