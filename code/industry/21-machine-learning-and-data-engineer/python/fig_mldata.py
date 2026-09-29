"""Chart data for Book 17, chapter 21."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_mldata as a  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
LABEL = {"ml and data": "machine learning and data", "software engineer": "software engineer",
         "quant developer": "quant developer", "risk": "risk", "quant researcher": "quantitative researcher",
         "trader": "trader"}
c = a.counts()
with open(OUT / "counts.csv", "w") as f:
    f.write("pos,family,n2021,lo2021,hi2021,n2025,lo2025,hi2025\n")
    for i, fam in enumerate(a.FAMILIES):
        v = []
        for fy in (2021, 2025):
            lo, hi = a.fr.poisson_interval(c[(fy, fam)])
            v += [str(c[(fy, fam)]), f"{lo:.1f}", f"{hi:.1f}"]
        f.write(f"{i + 1},{LABEL[fam]}," + ",".join(v) + "\n")
t = a.trends()
with open(OUT / "growth.csv", "w") as f:
    f.write("pos,family,annual,lo,hi\n")
    for i, fam in enumerate(reversed(a.FAMILIES)):
        x = t[fam]
        f.write(f"{i + 1},{LABEL[fam]},{100 * x['annual']:.2f},{100 * x['lo']:.2f},{100 * x['hi']:.2f}\n")
g = a.gaps()
with open(OUT / "gap.csv", "w") as f:
    f.write("pos,level,diff,lo,hi\n")
    for i, lv in enumerate(("all",) + a.LEVELS):
        x = g[lv]
        f.write(f"{i + 1},{lv},{x['diff'] / 1000:.2f},{x['diff_lo'] / 1000:.2f},{x['diff_hi'] / 1000:.2f}\n")
s = a.survey()
NAMES = {"52": "finance and insurance", "51": "information", "54": "professional and technical services",
         "5220A1": "banks (credit intermediation)", "524100": "insurance carriers", "523000": "securities",
         "513200": "software publishers"}
with open(OUT / "survey.csv", "w") as f:
    f.write("pos,industry,employment,median\n")
    for i, k in enumerate(reversed(("54", "52", "51", "524100", "5220A1", "523000", "513200"))):
        f.write(f"{i + 1},{NAMES[k]},{int(s[k]['employment']) / 1000:.2f},{float(s[k]['p50']) / 1000:.0f}\n")
