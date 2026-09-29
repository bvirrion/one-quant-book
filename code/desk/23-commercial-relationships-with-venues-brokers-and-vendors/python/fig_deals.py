"""Chart data for Book 16, chapter 23 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_deals as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "value.csv", "w") as f:
    f.write("share,net\n")
    for a, v in m.curve():
        f.write(f"{100 * a:.2f},{v / 1000:.3f}\n")

cases = {"small firm, published terms": m.deal(m.SMALL, m.R_SMALL),
         "small firm, tailored terms": m.deal(m.SMALL, m.R_SMALL, prog=m.tailored(m.SMALL)),
         "large firm, published terms": m.deal(m.LARGE, m.R_LARGE)}
with open(OUT / "zopa.csv", "w") as f:
    f.write("pos,case,low,high,nash\n")
    for i, (k, d) in enumerate(cases.items()):
        lo, hi = d["zopa"]
        nash = d["transfer"] if d["transfer"] is not None else float("nan")
        f.write(f"{i},{k.replace(',', ';')},{lo / 1000:.3f},{hi / 1000:.3f},{nash / 1000:.3f}\n")

b = cases["large firm, published terms"]
g, c = b["venue_gain"] / 1000, b["cost"] / 1000
rf = m.R_LARGE / 1000
with open(OUT / "pareto.csv", "w") as f:
    f.write("firm,venue,point\n")
    f.write(f"{0.0 - c + 0.0:.3f},{g:.3f},frontier\n{g - c:.3f},0.000,frontier\n")
    f.write(f"{rf:.3f},0.000,reservation\n")
    f.write(f"{b['transfer'] / 1000 - c:.3f},{g - b['transfer'] / 1000:.3f},nash\n")
