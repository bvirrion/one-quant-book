"""Chart data for Book 10, chapter 23 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_otc import NS, RHOS, dgp_study, rfq_study  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

d = dgp_study()
with open(OUT / "dgp.csv", "w") as f:
    f.write("rho,spread_bp\n")
    for rho in RHOS:
        f.write(f"{rho:g},{d[rho]['spread_share'] * 1e4:.3f}\n")
r = rfq_study()
with open(OUT / "rfq.csv", "w") as f:
    f.write("n,l025,l05,l1,l2\n")
    for i, n in enumerate(NS):
        f.write(f"{n}," + ",".join(f"{r[k]['curve'][i]:.3f}" for k in (0.25, 0.5, 1.0, 2.0)) + "\n")
