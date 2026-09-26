"""Chart data for Book 11, chapter 29 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hf_venues as h  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

pb = h.playbook()
with open(OUT / "playbook.csv", "w") as f:
    f.write("i,venue,picked_home,picked_own,edge_home,edge_own,msgs_home,msgs_own,vol_home,vol_own\n")
    for i, (k, v) in enumerate(pb.items()):
        a, b = v["home"], v["own"]
        f.write(f"{i},{k},{100 * a['picked'] / a['volume']:.1f},{100 * b['picked'] / b['volume']:.1f},"
                f"{a['edge']:.3f},{b['edge']:.3f},{a['messages']:.0f},{b['messages']:.0f},"
                f"{a['volume']:.0f},{b['volume']:.0f}\n")

with open(OUT / "budget.csv", "w") as f:
    f.write("gap,orders,rejects,accepted,volume\n")
    for r in h.budget_curve():
        f.write(f"{r['gap']},{r['orders']:.1f},{r['rejects']:.1f},{r['orders'] - r['rejects']:.1f},"
                f"{r['volume'] / 1000:.3f}\n")
