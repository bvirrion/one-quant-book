"""Chart data for Book 16, chapter 26 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_culture as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

q, y, P = m.year()
series = {"f1": P[0], "f5": P[4], "agg": m.dl.aggregate(P, "logodds")}
for name, p in series.items():
    with open(OUT / f"calib_{name}.csv", "w") as f:
        f.write("forecast,observed,count\n")
        for a, b, c in m.dl.calibration(p, y, 10):
            f.write(f"{a:.4f},{b:.4f},{c}\n")

indep, byrho = m.five_or_one()
with open(OUT / "rho.csv", "w") as f:
    f.write("rho,one,independent\n")
    for r, v in byrho.items():
        f.write(f"{r:.2f},{v:.5f},{indep:.5f}\n")

s = m.scores()
order = [f"forecaster {k}" for k in range(1, 6)] + ["mean", "log-odds", "extremised", "truth"]
with open(OUT / "brier.csv", "w") as f:
    f.write("pos,rule,brier\n")
    for i, k in enumerate(order):
        f.write(f"{i},{k},{s[k]:.4f}\n")
