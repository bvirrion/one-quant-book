"""Chart data for Book 6, chapter 9 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rc_bermudan import EUR, EXERCISES, bermudan_summary, boundary, par10  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

b = bermudan_summary()
with open(OUT / "europeans.csv", "w") as f:
    f.write("e,euro,berm\n")
    for e, v in zip(EXERCISES, b["euro_tree"], strict=True):
        f.write(f"{e},{1e4 * v:.3f},{1e4 * b['bermudan']:.3f}\n")
k = par10()
with open(OUT / "boundary.csv", "w") as f:
    f.write("e,rstar,strike,fwd\n")
    for e, r in boundary():
        fwd = EUR.df_t(float(e)) / EUR.df_t(float(e) + 1) - 1
        f.write(f"{e},{100 * r:.4f},{100 * k:.4f},{100 * fwd:.4f}\n")
