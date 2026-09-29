"""Chart data for Book 16, chapter 13 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_ops as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "late.csv", "w") as f:
    f.write("team,d10,d4,d25\n")
    for c in range(11, 21):
        row = [100 * m.om.p_late(m.LAM, m.MU, c, d) for d in (10.0, 4.0, 2.5)]
        f.write(f"{c}," + ",".join(f"{x:.4f}" for x in row) + "\n")

labels = ["under 30 min", "30 min to 1 h", "1 to 2 h", "2 to 4 h", "over 4 h"]
ages = {c: m.ageing(c) for c in (11, 12, 14)}
with open(OUT / "ageing.csv", "w") as f:
    f.write("pos,bucket,c11,c12,c14\n")
    for i, lab in enumerate(labels):
        f.write(f"{i},{lab}," + ",".join(f"{100 * ages[c][i]:.3f}" for c in (11, 12, 14)) + "\n")

with open(OUT / "cost.csv", "w") as f:
    f.write("team,staff,fail,total\n")
    for c, y in m.table("T+1", extra=8).items():
        f.write(f"{c},{c * m.STAFF_COST / 1e6:.4f},{y['fail_cost']:.4f},{y['total']:.4f}\n")

with open(OUT / "scenarios.csv", "w") as f:
    f.write("pos,scenario,staff,fail\n")
    for i, (k, v) in enumerate(m.scenarios().items()):
        f.write(f"{i},{k.replace(',', ';')},{v['staff']:.4f},{v['fail_cost']:.4f}\n")
