"""Chart data for Book 11, chapter 22 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hf_rfq as h  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "dealers.csv", "w") as f:
    f.write("n,pnl,naive,win\n")
    for n, r in h.equilibria().items():
        f.write(f"{n},{r['pnl']:.3f},{r['naive_pnl']:.3f},{100 * r['win']:.2f}\n")

w = h.win_model()
with open(OUT / "winmodel.csv", "w") as f:
    f.write("markup,empirical,fitted\n")
    for m, emp in w["bins"]:
        fit = 1.0 / (1.0 + h.np.exp(-(w["a"] + w["b"] * m)))
        f.write(f"{m:g},{emp:.4f},{fit:.4f}\n")
