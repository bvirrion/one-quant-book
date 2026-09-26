"""Chart data for Book 10, chapter 5 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_decomp import by_horizon, day, estimators, truth, var_by_lags  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

d = day()
with open(OUT / "horizon.csv", "w") as f:
    f.write("h,realised,impact,se,clean,clean_se\n")
    for h, v in by_horizon(d).items():
        f.write(f"{h},{v['realised']:.4f},{v['impact']:.4f},{v['se']:.4f},{v['clean']:.4f},{v['clean_se']:.4f}\n")

tr, e, lags = truth(d), estimators(d), var_by_lags(d)
rows = [("truth", tr["share"]), ("realised60", e["realised_60s"]), ("gh", e["gh_100"]),
        ("hs", e["huang_stoll"]), ("mrr", e["mrr"])]
rows += [(f"var{k[0]}", v) for k, v in lags.items()]
with open(OUT / "estimators.csv", "w") as f:
    f.write("k,name,share\n")
    for k, (name, x) in enumerate(rows):
        f.write(f"{k},{name},{x:.4f}\n")
