"""Chart data for Book 9, chapter 20 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_mbsrv import SHIFTS, io_scenarios, stack  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

g = io_scenarios()["gain"]
with open(OUT / "io.csv", "w") as f:
    f.write("shift,market,view,slow,noburnout\n")
    for i, s in enumerate(SHIFTS):
        f.write(f"{s},{g['market'][i]:.2f},{g['view'][i]:.2f},{g['slow'][i]:.2f},{g['no_burnout'][i]:.2f}\n")
with open(OUT / "oas.csv", "w") as f:
    f.write("coupon,market,view,noburnout\n")
    for r in stack():
        f.write(f"{r['coupon']:.1f},50.00,{r['oas_view']:.2f},{r['oas_nob']:.2f}\n")
