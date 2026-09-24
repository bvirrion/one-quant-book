"""Chart data for Chapter 22 (deterministic)."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/calendar"))
from div_implied import REGIONS_2025, implied_growth
from firm_calendar import load, utc_intervals

ROOT = pathlib.Path(__file__).resolve().parents[4]
OUT = ROOT / "figdata/markets-1/22-index-and-single-stock-futures-worldwide"
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "regions.csv", "w") as f:
    f.write("region,contracts_bn,share_pct\n")
    total = sum(v for _, v in REGIONS_2025)
    f.writelines(f"{k},{v:.2f},{v / total * 100:.1f}\n" for k, v in REGIONS_2025)

STRIP = [168.0, 171.5, 169.0, 166.0, 164.5, 163.5]           # illustrative annual dividend futures, points
with open(OUT / "strip.csv", "w") as f:
    f.write("year,points,growth_pct\n")
    g = [float("nan")] + implied_growth(STRIP)
    for i, p in enumerate(STRIP):
        f.write(f"{2026 + i},{p:.1f},{'nan' if i == 0 else f'{g[i] * 100:.2f}'}\n")

sessions = load(str(ROOT / "data/markets-1/sessions_sample.csv"))
with open(OUT / "relay.csv", "w") as f:              # line segments for pgfplots: nan rows break the line
    f.write("hour,row\n")
    for row, root in enumerate(("ES", "FESX", "HSI"), start=1):
        for a, b in utc_intervals(sessions, root, dt.date(2026, 9, 16)):
            end = 24.0 if b.date() > a.date() else b.hour + b.minute / 60
            f.write(f"{a.hour + a.minute / 60:.3f},{row}\n{end:.3f},{row}\nnan,nan\n")
