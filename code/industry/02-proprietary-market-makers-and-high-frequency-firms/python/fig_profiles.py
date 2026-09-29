"""Chart data for Book 17, chapter 2 (deterministic, from the committed tables)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_profiles as p  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

cov = p.coverage()
order = sorted(cov, key=lambda k: (-cov[k], k))
with open(OUT / "coverage.csv", "w") as f:
    f.write("k,firm,listed,private\n")
    for k, firm in enumerate(order):
        n = cov[firm]
        f.write(f"{k},{firm},{n if firm in p.LISTED else 0},{0 if firm in p.LISTED else n}\n")

with open(OUT / "cme.csv", "w") as f:
    f.write("k,year,globex,open_outcry,privately_negotiated\n")
    for k, r in enumerate(p.cme()):
        g, o, n = (r[c] / 1000 for c in ("globex", "open_outcry", "privately_negotiated"))
        f.write(f"{k},{r['year']},{g:.3f},{o:.3f},{n:.3f}\n")
