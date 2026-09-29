"""Chart data for Book 17, chapter 16 (fixed seeds)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_trader as a  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

cells, oews = a.pay()
with open(OUT / "pay.csv", "w") as f:
    f.write("pos,source,p10,p25,p50,p75,p90\n")
    q = ("p10", "p25", "p50", "p75", "p90")
    rows = [("OEWS sales agents in securities firms", {k: float(oews[k]) for k in q}),
            ("LCA traders at banks", cells["all"]["bank"]),
            ("LCA traders at market makers", cells["all"]["market maker"])]
    for i, (name, c) in enumerate(rows):
        f.write(f"{i + 1},{name}," + ",".join(f"{c[k] / 1000:.1f}" for k in q) + "\n")

with open(OUT / "tails.csv", "w") as f:
    f.write("n,mm1,lognormal\n")
    for n, m, s in a.tails():
        f.write(f"{n},{100 * m:.3f},{100 * s:.3f}\n")

one, five = a.capacity()
with open(OUT / "capacity.csv", "w") as f:
    f.write("pos,rate,one_minute,five_minutes\n")
    for i, r in enumerate(a.RATES):
        f.write(f"{i + 1},{r},{one[r]},{five[r]}\n")
