"""Chart data for Book 6, chapter 5 (deterministic)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "code/firm/sabrcube"))
from firm_sabrcube import normal_vol  # noqa: E402
from rc_sabrcube import NEG_F, NEG_T, TENORS, density_table, matrix_table, neg_fits, neg_quotes  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

fits = neg_fits()
with open(OUT / "negsmile.csv", "w") as f:
    f.write("k,s1,s3,nrm\n")
    for x in range(-95, 81, 2):
        k = x * 1e-4
        vals = []
        for name in ("shift0.01", "shift0.03", "normal"):
            p = fits[name][0]
            ok = name == "normal" or k > -p.shift + 5e-5
            vals.append(1e4 * normal_vol(NEG_F, k, NEG_T, p, "normal" if name == "normal" else "shifted") if ok
                        else float("nan"))
        f.write(f"{x / 100:.2f}," + ",".join("nan" if math.isnan(v) else f"{v:.3f}" for v in vals) + "\n")
ks, q = neg_quotes()
with open(OUT / "negquotes.csv", "w") as f:
    f.write("k,vol\n")
    for k, v in zip(ks, q, strict=True):
        f.write(f"{100 * k:.2f},{1e4 * v:.3f}\n")

with open(OUT / "density.csv", "w") as f:
    f.write("k,s1,s3,nrm\n")
    for row in density_table():
        f.write(f"{row[0]:.2f}," + ",".join("nan" if math.isnan(v) else f"{v:.3f}" for v in row[1:]) + "\n")

with open(OUT / "matrix.csv", "w") as f:
    f.write("e," + ",".join(f"n{n}" for n in TENORS) + "\n")
    for row in matrix_table():
        f.write(",".join(f"{v:.3f}" for v in row) + "\n")
