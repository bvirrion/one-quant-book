"""Chart data for Book 12, chapter 9 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ml_xsnet import cae, ipca, pca, truth  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/ml" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "total.csv", "w") as f:
    f.write("K,pca,ipca,cae,truth\n")
    for K in (1, 3, 5):
        f.write(f"{K},{100 * pca(K)[0]:.3f},{100 * ipca(K)[0]:.3f},{100 * cae(K)[0]:.3f},{100 * truth()[0]:.3f}\n")
with open(OUT / "recovery.csv", "w") as f:
    f.write("i,model,all,nonlinear\n")
    for i, (name, res) in enumerate((("PCA", pca(3)), ("IPCA", ipca(3)), ("CA", cae(3)))):
        f.write(f"{i},{name},{res[2][0]:.4f},{res[2][1]:.4f}\n")
