"""Chart data for Book 16, chapter 11 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_ip as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

names = list(m.CASES)
series, fits = {}, {}
for k, (_, hl) in m.CASES.items():
    months, edge = m.edge_series(hl, 11 + int(hl))
    est, level = m.gl.half_life_from_series(months, edge)
    series[k] = edge
    fits[k] = level * 0.5 ** (months / est)
with open(OUT / "edge.csv", "w") as f:
    f.write("month," + ",".join(names) + "," + ",".join(f"fit_{k}" for k in names) + "\n")
    for i, mo in enumerate(months):
        f.write(f"{mo}," + ",".join(f"{series[k][i]:.4f}" for k in names) + ","
                + ",".join(f"{fits[k][i]:.4f}" for k in names) + "\n")

t, prot, cost = m.curves()
with open(OUT / "protected.csv", "w") as f:
    f.write("years," + ",".join(names) + ",cost\n")
    for i, x in enumerate(t):
        f.write(f"{x:.3f}," + ",".join(f"{prot[k][i]:.4f}" for k in names) + f",{cost[i]:.4f}\n")
