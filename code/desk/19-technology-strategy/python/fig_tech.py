"""Chart data for Book 16, chapter 19 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_tech as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "virtu.csv", "w") as f:
    f.write("year,revenue,comm_data,share\n")
    for y, rev, cd in m.virtu():
        f.write(f"{y},{rev:.1f},{cd:.1f},{100 * cd / rev:.2f}\n")

with open(OUT / "profits.csv", "w") as f:
    f.write("pos,strategy,t1,t2,t3\n")
    for i, (k, v) in enumerate(m.choices().items()):
        f.write(f"{i},{k}," + ",".join(f"{x:.3f}" for x in v["profits"]) + "\n")

with open(OUT / "race.csv", "w") as f:
    f.write("pos,strategy,spend,baseline\n")
    for i, (k, v) in enumerate(m.races().items()):
        f.write(f"{i},{k},{v['spend']:.3f},{v['baseline']:.3f}\n")
