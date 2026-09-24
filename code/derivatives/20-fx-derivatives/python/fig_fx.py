"""Chart data for Book 5, Chapter 20 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_fx import BARRIERS, leverage, one_touches, tarf_scenario, tarf_summary, vv_smile

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

v = vv_smile()
with open(OUT / "smile.csv", "w") as f:
    f.write("k,market,vv\n")
    for k, a, b in zip(v["ks"], v["market"], v["vv"], strict=True):
        f.write(f"{k:.4f},{100 * a:.4f},{100 * b:.4f}\n")
q = v["q"]
with open(OUT / "pillars.csv", "w") as f:
    f.write("k,vol\n")
    for k, vol in ((q["k25p"], q["v25p"]), (q["k_atm"], q["atm"]), (q["k25c"], q["v25c"])):
        f.write(f"{k:.4f},{100 * vol:.4f}\n")

ot = one_touches()
with open(OUT / "one_touch.csv", "w") as f:
    f.write("h,bs,vv,lv,slv,sv\n")
    for i, h in enumerate(BARRIERS):
        f.write(f"{h:.2f},{100 * ot['bs'][i]:.3f},{100 * ot['vv'][i]:.3f},{100 * ot['mix0.0'][i]:.3f},"
                f"{100 * ot['mix0.5'][i]:.3f},{100 * ot['mix1.0'][i]:.3f}\n")

_, (times, table) = leverage(0.5)
rows = [table[round(t * 252) - 1] for t in (0.25, 0.5, 1.0)]
with open(OUT / "leverage_axes.csv", "w") as f:
    f.write("s3m,l3m,s6m,l6m,s12m,l12m\n")
    for j in range(len(rows[0][0])):
        f.write(",".join(f"{rows[i][0][j]:.4f},{rows[i][1][j]:.4f}" for i in range(3)) + "\n")

s = tarf_summary()
with open(OUT / "tarf_fixings.csv", "w") as f:
    f.write("n,share\n")
    for n, c in enumerate(s["fixings_hist"]):
        if n > 0:
            f.write(f"{n},{100 * c / s['fixings_hist'].sum():.3f}\n")
with open(OUT / "tarf_scenarios.csv", "w") as f:
    f.write("move,pnl\n")
    for mv in (-0.05, -0.025, 0.0, 0.025, 0.05, 0.075, 0.10):
        f.write(f"{100 * mv:.1f},{tarf_scenario(mv)['pnl_mean'] / 1e6:.4f}\n")
