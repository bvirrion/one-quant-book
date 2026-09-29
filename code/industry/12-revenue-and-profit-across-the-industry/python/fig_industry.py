"""Chart data for Book 17, chapter 12 (reads the committed panel)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_industry as a  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
SHORT = {"Quadrature Capital Limited": "Quadrature", "Hudson River Trading Europe Ltd": "HRT Europe (UK entity)",
         "Intercontinental Exchange": "ICE", "Cboe Global Markets": "Cboe", "Virtu Financial": "Virtu",
         "Interactive Brokers": "Interactive Brokers"}

ph = a.per_head()
fr = a.firm_ranges(ph)
with open(OUT / "firm_ranges.csv", "w") as f:
    f.write("pos,firm,lo,hi,last\n")
    for i, r in enumerate(fr):
        f.write(f"{i + 1},{SHORT.get(r['firm'], r['firm'])},{r['lo']:.3f},{r['hi']:.3f},{r['last_v']:.3f}\n")

bf = a.by_firm(ph)
LINES = ("Virtu Financial", "Flow Traders", "CME Group", "Goldman Sachs", "Nasdaq")
with open(OUT / "series.csv", "w") as f:
    f.write("year,vix," + ",".join(SHORT.get(x, x).replace(" ", "_") for x in LINES) + "\n")
    v = a.vix()
    for y in range(2019, 2026):
        vals = [f"{bf[x]['years'][y]:.3f}" if y in bf[x]["years"] else "nan" for x in LINES]
        f.write(f"{y},{v[y]:.2f}," + ",".join(vals) + "\n")

fit = a.fit(ph)
KINDS = ("market maker", "exchange or venue", "asset manager", "bank (whole firm)", "broker", "crypto exchange")
with open(OUT / "elasticities.csv", "w") as f:
    f.write("pos,kind,b,err\n")
    for i, k in enumerate(KINDS):
        b, se = fit[k]
        f.write(f"{i + 1},{k.replace(' (whole firm)', '')},{b:.3f},{2 * se:.3f}\n")
