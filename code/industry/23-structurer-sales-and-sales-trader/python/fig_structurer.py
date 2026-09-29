"""Chart data for Book 17, chapter 23."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_structurer as a  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
m = a.margins()
with open(OUT / "coupon.csv", "w") as f:
    f.write("pos,rate,vol,fair,zero,margin6\n")
    for i, (r, v) in enumerate(((0.01, 0.2), (0.04, 0.2), (0.01, 0.3), (0.04, 0.3))):
        x = m[(r, v)]
        f.write(f"{i + 1},{r},{v},{x['fair_coupon']:.3f},{x['zero_margin_coupon']:.3f},{x['margin']:.3f}\n")
sh = a.eusipa_shares()
with open(OUT / "eusipa.csv", "w") as f:
    f.write("pos,market,bn,share\n")
    for i, k in enumerate(sorted(a.EUSIPA_OUTSTANDING, key=a.EUSIPA_OUTSTANDING.get)):
        f.write(f"{i + 1},{k},{a.EUSIPA_OUTSTANDING[k] / 1000:.1f},{100 * sh[k]:.1f}\n")
s = a.survey()
with open(OUT / "survey.csv", "w") as f:
    f.write("pos,label,p10,p25,p50,p75,p90\n")
    for i, (lab, k) in enumerate((("banks", "5220A1"), ("finance and insurance", "52"), ("securities", "523000"))):
        vals = ",".join(f"{float(s[k][q]) / 1000:.1f}" for q in ("p10", "p25", "p50", "p75", "p90"))
        f.write(f"{i + 1},{lab},{vals}\n")
