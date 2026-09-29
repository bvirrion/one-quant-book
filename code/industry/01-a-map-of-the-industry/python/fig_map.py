"""Chart data for Book 17, chapter 1 (deterministic, from the committed tables)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_map as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "registrations.csv", "w") as f:
    f.write("year,bd,ia_only\n")
    for r in m.finra():
        f.write(f"{r['year']},{(r['bd_only'] + r['dual']) / 1000:.3f},{r['ia_only'] / 1000:.3f}\n")

acc = m.accuracy()
with open(OUT / "accuracy.csv", "w") as f:
    f.write("k,rule,coarse,fine\n")
    for k, (rule, d) in enumerate(acc.items()):
        coarse, fine = 100 * d["coarse"][0] / d["coarse"][1], 100 * d["fine"][0] / d["fine"][1]
        f.write(f"{k},{rule.replace(',', '')},{coarse:.1f},{fine:.1f}\n")
