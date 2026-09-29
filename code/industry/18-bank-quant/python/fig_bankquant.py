"""Chart data for Book 17, chapter 18."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_bankquant as a  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
q = ("p10", "p25", "p50", "p75", "p90")
c = a.lca()
o = a.oews()


def k(x):
    return f"{float(x) / 1000:.1f}"


with open(OUT / "levels.csv", "w") as f:
    f.write("level,qr2021,qr2025,risk2025\n")
    for j, lvl in enumerate(a.LEVELS):
        vals = [c.get((fy, role, lvl)) for fy, role in ((2021, "quant researcher"), (2025, "quant researcher"),
                                                        (2025, "risk"))]
        f.write(f"{j + 1}," + ",".join("nan" if v is None or v["suppressed"] else k(v["p50"]) for v in vals) + "\n")
rows = [("survey: risk specialists; banks", o[("5220A1", "13-2054")]),
        ("survey: risk specialists; securities", o[("523000", "13-2054")]),
        ("survey: other financial specialists; securities", o[("523000", "13-2099")]),
        ("filings: bank risk roles", c[(2025, "risk", "all")]),
        ("filings: bank quant researchers", c[(2025, "quant researcher", "all")])]
with open(OUT / "ranges.csv", "w") as f:
    f.write("pos,label," + ",".join(q) + "\n")
    for i, (label, r) in enumerate(rows):
        f.write(f"{i + 1},{label}," + ",".join(k(r[x]) for x in q) + "\n")
with open(OUT / "headcount.csv", "w") as f:
    f.write("tier1_pct,validators\n")
    for s, h in a.curve():
        f.write(f"{100 * s:.0f},{h:.2f}\n")
inv = a.inventory()
with open(OUT / "base.csv", "w") as f:
    f.write("tier1_pct,validators\n")
    f.write(f"{inv[1] / 10:.1f},{a.headcount(inv):.2f}\n")
hours = a.by_tier(inv)
total = sum(hours.values())
with open(OUT / "tiers.csv", "w") as f:
    f.write("tier,models_pct,hours_pct\n")
    for t in (1, 2, 3):
        f.write(f"{t},{100 * inv[t] / a.MODELS:.1f},{100 * hours[t] / total:.1f}\n")
