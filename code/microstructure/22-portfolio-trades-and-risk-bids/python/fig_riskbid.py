"""Chart data for Book 10, chapter 22 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_riskbid import MARGIN, RISK_K, bids, blind  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

b = bids()
bl = blind()
rows = (("1", b["disclosed_true"]["cost"], RISK_K * b["disclosed_true"]["risk_hedged"], b["disclosed"]["curse"]),
        ("0", bl["cost"][0], RISK_K * bl["risk"][0], b["blind"]["curse"]))
with open(OUT / "bids.csv", "w") as f:
    f.write("y,cost,risk,curse,margin\n")
    for y, c, r, s in rows:
        f.write(f"{y},{c:.3f},{r:.3f},{s:.3f},{MARGIN:.3f}\n")
with open(OUT / "profile.csv", "w") as f:
    f.write("i,share\n")
    for i, s in enumerate(bl["profile"]["buckets"][:6]):
        f.write(f"{i},{100 * s:.2f}\n")
