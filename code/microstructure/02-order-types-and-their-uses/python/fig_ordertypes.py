"""Chart data for Book 10, chapter 2 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_ordertypes import iceberg_study, stop_cascade  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "cascade.csv", "w") as f:
    f.write("n,stop_market,stop_limit\n")
    for n in (0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20):
        f.write(f"{n},{stop_cascade(n)['drop_cents']},{stop_cascade(n, limit_offset=1)['drop_cents']}\n")

with open(OUT / "iceberg.csv", "w") as f:
    f.write("k,strict,loose,strict_fa,loose_fa\n")
    cases = [("venue", 0, 0.0), ("algo", 0, 0.0), ("algo", 200, 0.0), ("algo", 200, 0.3)]
    for k, (mode, d, j) in enumerate(cases):
        a = iceberg_study(mode, d, j)
        b = iceberg_study(mode, d, j, window_ms=1000, tol=0.35)
        f.write(f"{k},{a['rate']:.3f},{b['rate']:.3f},{a['false_alarms']},{b['false_alarms']}\n")
