"""Chart data for Book 5, Chapter 26 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_optmm import dividend_study, hedge_study, toy_mm, width_study

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

w = width_study()
rates = (0.0, 2.0, 5.0, 10.0, 20.0)
with open(OUT / "widths.csv", "w") as f:
    f.write("w," + ",".join(f"p{int(r)}" for r in rates) + "\n")
    for i, x in enumerate(w["grid"]):
        f.write(f"{x:.3f}," + ",".join(f"{w[r]['curve'][i]:.4f}" for r in rates) + "\n")
with open(OUT / "widths_opt.csv", "w") as f:
    f.write("informed,w,profit\n")
    for r in rates:
        f.write(f"{r:.0f},{w[r]['w_star']:.4f},{w[r]['profit']:.4f}\n")

h = hedge_study()
with open(OUT / "hedge_time.csv", "w") as f:
    f.write("every,cost,sd\n")
    for k, (c, sd, _) in h["time"].items():
        f.write(f"{k},{c:.4f},{sd:.4f}\n")
with open(OUT / "hedge_band.csv", "w") as f:
    f.write("c,cost,sd\n")
    for k, (c, sd, _) in h["band"].items():
        f.write(f"{k},{c:.4f},{sd:.4f}\n")

d = dividend_study()
with open(OUT / "dividend.csv", "w") as f:
    f.write("q,f10,f30,f50\n")
    for i in range(len(d[0.3]["curve"])):
        q = d[0.3]["curve"][i][0]
        f.write(f"{q / 1000:.1f}," + ",".join(f"{d[x]['curve'][i][1] / 1000:.3f}" for x in (0.1, 0.3, 0.5)) + "\n")
with open(OUT / "dividend_opt.csv", "w") as f:
    f.write("fail,q,net\n")
    for x in (0.1, 0.3, 0.5):
        f.write(f"{x},{d[x]['q'] / 1000:.3f},{d[x]['res']['net'] / 1000:.3f}\n")

on, off = toy_mm(limits=True), toy_mm(limits=False)
with open(OUT / "vega.csv", "w") as f:
    f.write("step,m3_on,m6_on,m3_off,m6_off\n")
    for i, (a, b) in enumerate(zip(on["vega_path"], off["vega_path"], strict=True)):
        f.write(f"{i + 1},{a['3m'] / 1000:.4f},{a['6m'] / 1000:.4f},{b['3m'] / 1000:.4f},{b['6m'] / 1000:.4f}\n")
