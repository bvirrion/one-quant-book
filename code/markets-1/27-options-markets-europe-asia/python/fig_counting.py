"""Chart data for Chapter 27 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from counting import MARKETS, REGIONS_2025, derive_2024, three_rankings

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/27-options-markets-europe-asia"
OUT.mkdir(parents=True, exist_ok=True)

r = three_rankings()
with open(OUT / "rankings.csv", "w") as f:
    f.write("market,contracts,notional,premium\n")
    for i, m in enumerate(MARKETS, start=1):
        cells = [f"{r[k][m.name] * 100:.1f}" for k in ("contracts", "notional_usd", "premium_usd")]
        f.write(f"M{i}," + ",".join(cells) + "\n")

prev = derive_2024()
with open(OUT / "regions.csv", "w") as f:
    f.write("region,y2024,y2025\n")
    f.writelines(f"{k},{prev[k]:.1f},{v:.1f}\n" for k, (v, _) in REGIONS_2025.items())
