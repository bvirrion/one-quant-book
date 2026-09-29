"""Chart data for Book 16, chapter 4 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_fund as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

ill = m.illiquid_ladder()
with open(OUT / "liquidity.csv", "w") as f:
    f.write("days,investor,portfolio,illiquid\n")
    for r in m.form_pf():
        d = int(r["days"])
        f.write(f"{d},{r['investor_pct']:.1f},{r['portfolio_pct']:.1f},{100 * m.ft.ladder_share_within(ill, d):.1f}\n")

rows = m.stress_table()
with open(OUT / "stress.csv", "w") as f:
    f.write("k,label,hf_dilution,ill_dilution,hf_liquid,ill_liquid\n")
    for k, lab in enumerate(("liquid first", "pro rata", "gate 10%", "liquid first, swing")):
        a, b = rows[("hedge funds", lab)], rows[("illiquid fund", lab)]
        name = lab.replace(",", ";").replace("%", " pct")
        f.write(f"{k},{name},{100 * a[2]:.2f},{100 * b[2]:.2f},{100 * a[3]:.1f},{100 * b[3]:.1f}\n")
