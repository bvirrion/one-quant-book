"""Chart data for Book 17, chapter 4 (deterministic, from the committed derived tables)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_quantfunds as q  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "rpe_hist.csv", "w") as f:
    f.write("mid,advisers\n")
    for r in q.hist():
        f.write(f"{(r['log10_lo'] + r['log10_hi']) / 2:.3f},{r['advisers']:.0f}\n")

with open(OUT / "named.csv", "w") as f:
    f.write("employees,raum_bn,label\n")
    for r in q.named():
        f.write(f"{r['employees']:.0f},{r['raum_bn']:.2f},{r['label'].replace(',', '')}\n")
