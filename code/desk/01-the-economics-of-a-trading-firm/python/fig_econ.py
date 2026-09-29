"""Chart data for Book 16, chapter 1 (deterministic, from the committed filings tables)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_econ as e  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "shares.csv", "w") as f:
    f.write("k,firm,volume,comp,fixed,profit\n")
    for k, (firm, d) in enumerate(e.latest_shares().items()):
        f.write(f"{k},{e.LABEL[firm]},{100 * d['volume']:.1f},{100 * d['comp']:.1f},{100 * d['fixed']:.1f},"
                f"{100 * d['profit']:.1f}\n")

with open(OUT / "virtu_years.csv", "w") as f:
    f.write("year,nr,comp,fixed,profit\n")
    for d in e.table("virtu"):
        f.write(f"{d['year']},{d['nr']:.1f},{d['comp']:.1f},{d['fixed']:.1f},{d['profit']:.1f}\n")

for firm in ("virtu", "man"):
    a, b, _ = e.pay_fit(firm)
    with open(OUT / f"pay_{firm}.csv", "w") as f:
        f.write("nr,comp,fit\n")
        for d in sorted(e.table(firm), key=lambda d: d["nr"]):
            f.write(f"{d['nr']:.1f},{d['comp']:.1f},{a + b * d['nr']:.1f}\n")

ch, curves = e.profit_curves()
with open(OUT / "cycle.csv", "w") as f:
    f.write("change," + ",".join(e.FIRMS) + "\n")
    for i, c in enumerate(ch):
        f.write(f"{100 * c:.0f}," + ",".join(f"{curves[k][i]:.3f}" for k in e.FIRMS) + "\n")
