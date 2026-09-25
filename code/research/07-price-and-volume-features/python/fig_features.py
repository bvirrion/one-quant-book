"""Chart data for Book 7, chapter 7 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_features import crossover_filter, ic_by_horizon, range_race  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

names = ("reversal 1d", "reversal 21d", "momentum 12-1", "momentum 12")
curves = {n: ic_by_horizon(n) for n in names}
with open(OUT / "horizon.csv", "w") as f:
    f.write("h,rev1,rev21,mom121,mom12\n")
    for h in curves[names[0]]:
        f.write(f"{h}," + ",".join(f"{curves[n][h]:.5f}" for n in names) + "\n")

with open(OUT / "filter.csv", "w") as f:
    f.write("lag,w520,w1050\n")
    a, b = crossover_filter(5, 20), crossover_filter(10, 50)
    for j in range(len(b)):
        f.write(f"{j + 1},{a[j] if j < len(a) else 0.0:.4f},{b[j]:.4f}\n")

cases = {"base": {}, "drift": {"drift": 0.005}, "gaps": {"gap_share": 0.3}}
res = {k: range_race(**v) for k, v in cases.items()}
est = ("close-to-close", "Parkinson", "Garman-Klass", "Rogers-Satchell", "Yang-Zhang (20 days)")
with open(OUT / "race.csv", "w") as f:
    f.write("k,estimator,base,drift,gaps\n")
    for i, e in enumerate(est):
        f.write(f"{i},{e.split(' ')[0]}," + ",".join(f"{res[c][e]['bias']:.4f}" for c in cases) + "\n")
print({e: round(res["base"][e]["efficiency"], 2) for e in est})
