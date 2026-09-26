"""Chart data for Book 10, chapter 20 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_wheel import MONTHS, power_study, thompson_study  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

p = power_study()
with open(OUT / "power.csv", "w") as f:
    f.write("months,adjusted,raw\n")
    for m, a, r in zip(MONTHS, p["power_adj"], p["power_raw"], strict=True):
        f.write(f"{m},{100 * a:.1f},{100 * r:.1f}\n")
t = thompson_study()
with open(OUT / "thompson.csv", "w") as f:
    f.write("month,thompson,uniform\n")
    for i, (a, b) in enumerate(zip(t["thompson"]["by_month"], t["uniform"]["by_month"], strict=True)):
        f.write(f"{i + 1},{100 * a:.1f},{100 * b:.1f}\n")
