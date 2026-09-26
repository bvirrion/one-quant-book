"""Chart data for Book 10, chapter 12 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_prop import KAPPAS, LAGS, kernel_family, kernel_study  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

k = kernel_study()
with open(OUT / "kernel.csv", "w") as f:
    f.write("lag,acf,response,G\n")
    for lag in (1, 2, 3, 5, 7, 10, 15, 20, 30, 50, 70, 100):
        f.write(f"{lag},{k['acf'][lag]:.5f},{k['response'][lag]:.5f},{k['G'][lag]:.5f}\n")
with open(OUT / "diffusion.csv", "w") as f:
    f.write("lag,market,model,shuffled\n")
    for i, lag in enumerate(LAGS):
        f.write(f"{lag},{k['var_market'][i]:.4f},{k['var_model'][i]:.4f},{k['var_shuffled'][i]:.4f}\n")
fam = kernel_family()
with open(OUT / "family.csv", "w") as f:
    f.write("kappa,round_trip,min_trade\n")
    for kap in KAPPAS:
        f.write(f"{kap},{fam[kap]['round_trip']:.5f},{fam[kap]['min_trade']:.5f}\n")
