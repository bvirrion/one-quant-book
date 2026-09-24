"""Chart data for Chapter 26 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from zero_day import atm_gamma_by_minutes, simulate_with_hedgers, straddle_price

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/gex"))
from firm_gex import YEAR_MINUTES, gamma

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/26-zero-day-options-and-retail-flow"
OUT.mkdir(parents=True, exist_ok=True)

minutes = [390 * 21, 390 * 10, 390 * 5, 390 * 2, 390, 240, 120, 60, 30, 15, 5]
with open(OUT / "atm_gamma.csv", "w") as f:
    f.write("minutes,delta_change_pct\n")
    gammas = atm_gamma_by_minutes(100.0, 0.16, minutes)
    f.writelines(f"{m},{g * 100:.2f}\n" for m, g in zip(minutes, gammas, strict=True))

with open(OUT / "gamma_profile.csv", "w") as f:
    f.write("spot,month,day,hour\n")
    for k in range(9400, 10601, 10):
        s = k / 100.0
        row = [gamma(s, 100.0, t, 0.16) * s * 0.01 * 100 for t in (21 / 252, 1 / 252, 60 / YEAR_MINUTES)]
        f.write(f"{s:.2f}," + ",".join(f"{x:.2f}" for x in row) + "\n")

with open(OUT / "feedback.csv", "w") as f:
    f.write("feedback,vol_ratio\n")
    for k in range(-6, 7):
        fb = k / 10.0
        f.write(f"{fb:.1f},{simulate_with_hedgers(4000, 78, 0.001, fb, 26):.3f}\n")

price = straddle_price(100.0, 0.16, 1 / 252)
with open(OUT / "straddle.csv", "w") as f:
    f.write("move_pct,pnl_pct\n")
    f.writelines(f"{m / 10:.1f},{abs(m / 10) - price:.3f}\n" for m in range(-25, 26))
