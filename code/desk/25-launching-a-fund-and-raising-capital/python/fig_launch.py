"""Chart data for Book 16, chapter 25 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_launch as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

q = m.fan()
with open(OUT / "fan.csv", "w") as f:
    f.write("month,p10,p25,p50,p75,p90\n")
    for i in range(q.shape[1]):
        f.write(f"{i + 1}," + ",".join(f"{x:.2f}" for x in q[:, i]) + "\n")

rc = m.reach_curve()
keys = list(rc)
with open(OUT / "reach.csv", "w") as f:
    f.write("month,seeded,unseeded\n")
    for i in range(60):
        f.write(f"{i + 1},{100 * rc[keys[0]][i]:.2f},{100 * rc[keys[1]][i]:.2f}\n")

s = m.summary()
with open(OUT / "values.csv", "w") as f:
    f.write("pos,case,manager,seeder\n")
    for i, (k, v) in enumerate(s.items()):
        name = k.replace(",", ";").replace("$", "USD ").replace("%", " pct")
        f.write(f"{i},{name},{v['manager']:.3f},{v['seeder']:.3f}\n")
