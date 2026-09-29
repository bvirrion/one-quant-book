"""Chart data for Book 17, chapter 20."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_engineer as a  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
g = a.kind_gaps()
cols = (("bank2021", 2021, "bank"), ("bank2025", 2025, "bank"), ("exch2025", 2025, "exchange"))
with open(OUT / "ratio.csv", "w") as f:
    f.write("pos,level," + ",".join(f"{c},{c}_lo,{c}_hi" for c, _, _ in cols) + "\n")
    for j, lv in enumerate(("all",) + a.LEVELS):
        vals = []
        for _, fy, other in cols:
            x = g.get((fy, other, lv))
            vals += ["nan"] * 3 if x is None else [f"{x['ratio']:.4f}", f"{x['ratio_lo']:.4f}", f"{x['ratio_hi']:.4f}"]
        f.write(f"{j + 1},{'all' if lv == 'all' else lv}," + ",".join(vals) + "\n")
s = a.survey()
names = (("search", "519200"), ("securities", "523000"), ("publishers", "513200"), ("banks", "5220A1"),
         ("systems", "541500"))
with open(OUT / "survey.csv", "w") as f:
    f.write("pos,percentile," + ",".join(n for n, _ in names) + "\n")
    for j, q in enumerate(a.Q):
        f.write(f"{j + 1},{q}," + ",".join(f"{float(s[k][q]) / 1000:.1f}" for _, k in names) + "\n")
c = a.cells()
LABEL = {"systematic fund": "systematic fund", "multi-manager platform": "platform", "market maker": "market maker",
         "bank": "bank", "exchange": "exchange"}
with open(OUT / "kinds.csv", "w") as f:
    f.write("pos,kind," + ",".join(a.Q) + "\n")
    for i, k in enumerate(reversed(a.KINDS)):
        f.write(f"{i + 1},{LABEL[k]}," + ",".join(f"{c[k][q] / 1000:.1f}" for q in a.Q) + "\n")
