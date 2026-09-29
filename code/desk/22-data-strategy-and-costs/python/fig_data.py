"""Chart data for Book 16, chapter 22 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_data as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "budget.csv", "w") as f:
    f.write("pos,category,cost\n")
    for i, (k, v) in enumerate(m.the_budget().items()):
        f.write(f"{i},{k},{v:.1f}\n")

with open(OUT / "enterprise.csv", "w") as f:
    f.write("users,per_user,enterprise\n")
    for n, a, b in m.reference_curve():
        f.write(f"{n},{a:.1f},{b:.1f}\n")

with open(OUT / "audit.csv", "w") as f:
    f.write("under,principal,interest\n")
    for u in (0.05, 0.10, 0.15, 0.20, 0.25, 0.30):
        _, a = m.audit(u)
        f.write(f"{100 * u:.0f},{a['principal']:.2f},{a['interest']:.2f}\n")
