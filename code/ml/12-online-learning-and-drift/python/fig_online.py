"""Chart data for Book 12, chapter 12 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ml_online import DETECTORS, DURATIONS, FLIP, LAMS, WARM, _gains, alarm_times, forgetting, thresholds  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/ml" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "forgetting.csv", "w") as f:
    f.write("memory," + ",".join(f"D{D}" for D in DURATIONS) + "\n")
    for lam in LAMS[1:]:
        mem = 1 / (1 - lam) if lam < 1 else 20000
        f.write(f"{mem:.0f}," + ",".join(f"{100 * forgetting(D)[lam]:.3f}" for D in DURATIONS) + "\n")

g = _gains(200, True)
flip = FLIP - WARM
th = thresholds()
with open(OUT / "gains.csv", "w") as f:
    f.write("step,running\n")
    c = np.cumsum(g)
    for t in range(49, len(g), 10):
        f.write(f"{t + WARM},{(c[t] - c[t - 49]) / 50:.4f}\n")
with open(OUT / "alarms.csv", "w") as f:
    f.write("step,level,detector\n")
    for k, (name, (make, _)) in enumerate(DETECTORS.items()):
        al = alarm_times(lambda make=make, name=name: make(th[name]), g)
        keep = [a for a in al if flip - 300 <= a < flip] + [a for a in al if a >= flip][:1]
        for a in keep:                                                   # false alarms shown, then the first true one
            f.write(f"{a + WARM},{1.6 - 0.35 * k:.2f},{k}\n")
