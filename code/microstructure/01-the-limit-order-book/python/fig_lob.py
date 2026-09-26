"""Chart data for Book 10, chapter 1 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_lob import depth_profile, fill_probability, session, zi_market  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

d = depth_profile(session())
with open(OUT / "depth.csv", "w") as f:
    f.write("k,bid,ask\n")
    for k in range(d.shape[1]):
        f.write(f"{k},{d[0, k]:.0f},{d[1, k]:.0f}\n")

sf, no = zi_market(improve=True), zi_market(improve=False)
with open(OUT / "fill.csv", "w") as f:
    f.write("n,formula,zi,zi_noimprove\n")
    for n in range(1, 9):
        f.write(f"{n},{fill_probability(n, 2.0, 0.05, 0.05):.4f},{sf['fill'][n][0]:.4f},{no['fill'][n][0]:.4f}\n")
