"""Chart data for Book 5, Chapter 18 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_autocall import PILLARS, cliff, fair_coupon, flat, price_vs_vol, sensitivities, worst_of

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

s = sensitivities()
fc = s["fair"]
with open(OUT / "outcomes.csv", "w") as f:
    f.write("i,label,prob\n")
    for j, p in enumerate(fc["call_probs"]):
        f.write(f"{j},{(j + 1) * 3}m,{100 * p:.3f}\n")
    f.write(f"{len(fc['call_probs'])},mat.,{100 * (fc['maturity_prob'] - fc['ki_prob']):.3f}\n")
    f.write(f"{len(fc['call_probs']) + 1},KI,{100 * fc['ki_prob']:.3f}\n")

with open(OUT / "vega.csv", "w") as f:
    f.write("i,pillar,vega\n")
    for i, (p, v) in enumerate(zip(PILLARS, s["vega_buckets"], strict=True)):
        f.write(f"{i},{p:.0f}y,{v:.4f}\n")
    f.write(f"3,all,{s['vega_parallel']:.4f}\n")
with open(OUT / "price_vol.csv", "w") as f:
    f.write("shift,price\n")
    for d, p in price_vs_vol():
        f.write(f"{100 * d:.0f},{p:.4f}\n")

wo = worst_of()
flat_fc = fair_coupon(flat(s["flat_vol"]))
with open(OUT / "coupons.csv", "w") as f:
    f.write("i,label,annual\n")
    rows = [("flat vol", flat_fc["annual"]), ("local vol", fc["annual"]), ("worst-of 0.7", wo[0.7]["annual"]),
            ("worst-of 0.5", wo[0.5]["annual"])]
    for i, (lab, a) in enumerate(rows):
        f.write(f"{i},{lab},{a:.3f}\n")

c = cliff()
spots, before, after_spots, after = c["curve"]
with open(OUT / "cliff_before.csv", "w") as f:
    f.write("s,delta\n")
    for x, d in zip(spots, before, strict=True):
        f.write(f"{100 * x:.3f},{d:.4f}\n")
with open(OUT / "cliff_after.csv", "w") as f:
    f.write("s,delta\n")
    for x, d in zip(after_spots, after, strict=True):
        f.write(f"{100 * x:.3f},{d:.4f}\n")
