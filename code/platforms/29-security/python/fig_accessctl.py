"""Chart data for One Quant Book 15, chapter 29 (deterministic: access logs seed 29, planted insiders seed 30)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_accessctl import (  # noqa: E402
    EXTRAS,
    access_logs,
    delays,
    plant,
    statistics,
    stolen_key_attempts,
    thresholds,
    toxic_summary,
)

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
SHORT = {"single day, trailing": "day_trailing", "CUSUM, trailing": "cusum_trailing",
         "single day, lagged": "day_lagged", "CUSUM, lagged": "cusum_lagged"}

h = thresholds()
with open(OUT / "thresholds.csv", "w") as f:
    f.write("detector,threshold\n")
    for name, v in h.items():
        f.write(f"{SHORT[name]},{v:.3f}\n")
with open(OUT / "detection.csv", "w") as f:
    f.write("extra_pct," + ",".join(f"{c}_found,{c}_median" for c in SHORT.values()) + "\n")
    for e in EXTRAS:
        r = delays(e, h=h)
        f.write(f"{100 * e:g}," + ",".join(f"{r[n][0]},{r[n][1]:.1f}" for n in SHORT) + "\n")
x = access_logs()
u, start = 42, 120
s = statistics(plant(x, u, start, 0.3)[u:u + 1])
clean = statistics(x[7:8])
with open(OUT / "insider.csv", "w") as f:
    f.write("day,cusum_lagged,cusum_trailing,clean_cusum_lagged\n")
    for d in range(90, 250):
        f.write(f"{d},{s['CUSUM, lagged'][0, d]:.3f},{s['CUSUM, trailing'][0, d]:.3f},"
                f"{clean['CUSUM, lagged'][0, d]:.3f}\n")
with open(OUT / "toxic.csv", "w") as f:
    t = toxic_summary()
    f.write("policy,toxic_roles,toxic_users\n")
    for name, v in t.items():
        f.write(f"{name},{len(v['roles'])},{len(v['users'])}\n")
with open(OUT / "keys.csv", "w") as f:
    f.write("attempt,accepted,reason\n")
    for name, ok, why in stolen_key_attempts():
        f.write(f"{name},{ok},{why.replace(',', ';')}\n")
assert np.isfinite(h["CUSUM, lagged"])
