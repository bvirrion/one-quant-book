"""Chart data for Book 17, chapter 24."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_control as a  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
g = a.ratios()
cols = (("bank2021", 2021, "bank"), ("bank2025", 2025, "bank"), ("trading2025", 2025, "trading firms"))
with open(OUT / "ratio.csv", "w") as f:
    f.write("pos,level," + ",".join(f"{c},{c}_lo,{c}_hi" for c, _, _ in cols) + "\n")
    for j, lv in enumerate(("all",) + a.LEVELS):
        vals = []
        for _, fy, scope in cols:
            x = g.get((fy, scope, lv))
            vals += ["nan"] * 3 if x is None else [f"{x['ratio']:.4f}", f"{x['ratio_lo']:.4f}", f"{x['ratio_hi']:.4f}"]
        f.write(f"{j + 1},{lv}," + ",".join(vals) + "\n")
e = a.eba()
AREAS = (("Retail banking", "retail banking"), ("Independent control functions", "independent control functions"),
         ("Investment banking", "investment banking"), ("Corporate functions", "corporate functions"),
         ("Asset management", "asset management"), ("MB Management function", "management body (executive)"),
         ("All other", "all other"))
with open(OUT / "eba.csv", "w") as f:
    f.write("pos,area,ratio,n\n")
    for i, (k, lab) in enumerate(sorted(AREAS, key=lambda x: -e[x[0]][1])):
        f.write(f"{i + 1},{lab},{e[k][1]:.3f},{e[k][0]}\n")
s = a.survey()
with open(OUT / "survey.csv", "w") as f:
    f.write("pos,label,p10,p25,p50,p75,p90\n")
    for i, (occ, lab) in enumerate(a.OCCS):
        vals = ",".join(f"{float(s[occ][q]) / 1000:.1f}" for q in ("p10", "p25", "p50", "p75", "p90"))
        f.write(f"{i + 1},{lab},{vals}\n")
