"""Chart data for Book 7, chapter 24 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_riskmodel import (  # noqa: E402
    START,
    YEAR,
    books,
    forecast,
    forecast_pca,
    fundamental,
    market_bias,
    rolling_bias,
    specific_deciles,
)

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

b, _ = books()
w = b["exposed"]
full = rolling_bias(*forecast(w, fundamental()))
nomom = rolling_bias(*forecast(w, fundamental("momentum"), omit="momentum"))
pca = rolling_bias(*forecast_pca(w))
mb = market_bias()
with open(OUT / "rolling.csv", "w") as f:
    f.write("year,full,nomom,pca,mkt_raw,mkt_vra\n")
    for i in range(0, len(full), 5):
        yr = (START + YEAR + i) / YEAR
        f.write(f"{yr:.3f},{full[i]:.4f},{nomom[i]:.4f},{pca[i]:.4f},{mb[False][1][i]:.4f},{mb[True][1][i]:.4f}\n")

sd = specific_deciles()
with open(OUT / "deciles.csv", "w") as f:
    f.write("decile,raw,shrunk\n")
    for d in range(10):
        f.write(f"{d + 1},{sd['spec_raw'][d]:.4f},{sd['spec'][d]:.4f}\n")
