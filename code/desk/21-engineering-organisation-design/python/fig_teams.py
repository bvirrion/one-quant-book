"""Chart data for Book 16, chapter 21 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_teams as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

c = m.compare_all()
with open(OUT / "designs.csv", "w") as f:
    f.write("pos,design,coordination,cross_edges,pages_max,pages_mean,bus_factor\n")
    for i, (k, v) in enumerate(c.items()):
        f.write(f"{i},{k},{v['coordination']:.2f},{v['cross_edges']},{v['pages_max']:.3f},{v['pages_mean']:.3f},"
                f"{v['bus_factor']}\n")

loads = {"embedded": m.tp.pages(m.services(), m.embedded()), "central": m.tp.pages(m.services(), m.central()),
         "consolidated": m.tp.pages(m.consolidated_services(), m.consolidated())}
short = {"trading platform": "platform"}
with open(OUT / "pages.csv", "w") as f:
    f.write("label,pages\n")
    for d, p in loads.items():
        seen = set()
        for t, v in p.items():
            name = "desk" if t in m.DESKS else short.get(t, t)
            if name not in seen:
                seen.add(name)
                f.write(f"{d}: {name},{v:.3f}\n")
