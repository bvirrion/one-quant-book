"""Chart data for Book 5, Chapter 6 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_american import HOOK, REF, bermudan_put, bs, exercise_decision, perpetual_put, premium_vs_rate, put_boundary

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

bd = put_boundary(100.0, 3.0, 0.05, 0.0, 0.20, n=3000)
s_star, _ = perpetual_put(100.0, 0.05, 0.20)
with open(OUT / "boundary.csv", "w") as f:
    f.write("tau,boundary,perpetual,strike\n")
    for tau, b in bd[:: 10]:
        f.write(f"{tau:.4f},{b:.4f},{s_star:.4f},100\n")

with open(OUT / "premium.csv", "w") as f:
    f.write("rate,american,premium\n")
    for r, am, prem in premium_vs_rate([i / 100 for i in range(0, 11)]):
        f.write(f"{100 * r:.0f},{am:.4f},{prem:.4f}\n")

with open(OUT / "decision.csv", "w") as f:
    f.write("div,exercise,hold\n")
    for i in range(0, 41):
        d = i * 0.025
        e = exercise_decision(HOOK["spot"], HOOK["strike"], d, HOOK["t_left"], HOOK["r"], HOOK["vol"])
        f.write(f"{d:.3f},{e['exercise']:.4f},{e['hold']:.4f}\n")

eu = bs(REF["spot"], REF["strike"], REF["t"], REF["r"], 0.0, REF["vol"], "P")
with open(OUT / "bermudan.csv", "w") as f:
    f.write("dates,bermudan,european\n")
    for m in (1, 2, 3, 4, 6, 12, 24, 50, 100, 200):
        f.write(f"{m},{bermudan_put(100.0, 100.0, 1.0, 0.05, 0.20, m):.4f},{eu:.4f}\n")
