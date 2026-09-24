"""Chart data for Book 2, Chapter 15 (deterministic, seeded)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lastlook_demo import THRESHOLD, by_hold

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-2/15-fx-spot-microstructure"
OUT.mkdir(parents=True, exist_ok=True)
asym, sym = by_hold("asymmetric", THRESHOLD), by_hold("symmetric", THRESHOLD)
with open(OUT / "hold.csv", "w") as f:
    f.write("hold,rej_inf_asym,rej_uninf_asym,rej_inf_sym,rej_uninf_sym,mo_asym,mo_sym\n")
    for (h, a), (_, s) in zip(asym, sym, strict=True):
        rej = [100 * x[k] for x in (a, s) for k in ("reject_informed", "reject_uninformed")]
        f.write(f"{h}," + ",".join(f"{v:.2f}" for v in rej) + f",{a['markout']:.4f},{s['markout']:.4f}\n")
