"""Chart data for Book 8, chapter 24 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_posisig import corn, lag_table  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "lags.csv", "w") as f:
    f.write("lag,hedge,spec\n")
    for lag, v in lag_table().items():
        f.write(f"{lag},{v['hedge'][0]:.4f},{v['spec'][0]:.4f}\n")

c = corn()
with open(OUT / "corn.csv", "w") as f:
    f.write("year,mm,pm\n")
    for d, a, b in zip(c["dates"], c["mm"], c["pm"], strict=True):
        f.write(f"{d.year + (d.timetuple().tm_yday - 1) / 365.25:.3f},{100 * a:.2f},{100 * b:.2f}\n")
