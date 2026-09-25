"""Chart data for Book 7, chapter 3 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_pit import payrolls, survivorship, vintage_store

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

def months_after(v, ref=(2008, 9)):
    y, m = (int(x) for x in v.split("-"))
    return 12 * (y - ref[0]) + (m - ref[1])

store = vintage_store()
with open(OUT / "life.csv", "w") as f:
    f.write("after,change\n")
    for known, value in store.vintages("US", "payrolls_change", "2008-09"):
        f.write(f"{months_after(known)},{value:.0f}\n")

p = payrolls()
with open(OUT / "y2008.csv", "w") as f:
    f.write("i,month,first,latest\n")
    for i, m in enumerate(p["month"]):
        if "2008-01" <= m <= "2009-12":
            f.write(f"{months_after(m, (2008, 1))},{m},{p['first'][i]:.0f},{p['latest'][i]:.0f}\n")

s = survivorship()
with open(OUT / "surv.csv", "w") as f:
    f.write("year,full,survivors\n")
    f.write("0,1,1\n")
    for t in range(len(s["cum_full"])):
        f.write(f"{(t + 1) / 12:.4f},{s['cum_full'][t]:.5f},{s['cum_surv'][t]:.5f}\n")
print("bias", round(s["bias"], 4), "final", round(float(s["cum_full"][-1]), 2), round(float(s["cum_surv"][-1]), 2),
      "life", [v for _, v in store.vintages("US", "payrolls_change", "2008-09")][:5])
