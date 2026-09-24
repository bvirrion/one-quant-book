"""Chart data for Book 3, Chapter 6 (deterministic, from data/markets-3)."""
import datetime as dt
import pathlib
import sys
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_trading import battery_day, battery_plan, load

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

rows = load()
month: dict[tuple[int, int], list[tuple[float, float]]] = defaultdict(list)
for t, p, s, _ in rows:
    month[(t.year, t.month)].append((p, s))
with open(OUT / "capture.csv", "w") as f:
    f.write("t,base,solar\n")
    for (y, m), v in sorted(month.items()):
        base = sum(p for p, _ in v) / len(v)
        sol = sum(p * s for p, s in v) / sum(s for _, s in v)
        f.write(f"{y + (m - 0.5) / 12:.4f},{base:.2f},{sol:.2f}\n")

day = [p for t, p, _, _ in rows if t.date() == dt.date(2025, 6, 18)]
_, acts = battery_plan(day)
soc = 0
with open(OUT / "batteryday.csv", "w") as f:
    f.write("hour,price,soc,tend\n")
    for h, (p, a) in enumerate(zip(day, acts, strict=True)):
        soc += 100 * a
        f.write(f"{h},{p:.2f},{soc},{h + 0.5}\n")

by_day: dict[dt.date, list[float]] = defaultdict(list)
for t, p, _, _ in rows:
    by_day[t.date()].append(p)
cum = {2024: 0.0, 2025: 0.0}
with open(OUT / "batterycum.csv", "w") as f:
    f.write("doy,y2024,y2025\n")
    for doy in range(1, 366):
        for y in (2024, 2025):
            d = dt.date(y, 1, 1) + dt.timedelta(days=doy - 1)
            cum[y] += battery_day(by_day[d]) / 100.0 / 1000.0
        f.write(f"{doy},{cum[2024]:.3f},{cum[2025]:.3f}\n")
