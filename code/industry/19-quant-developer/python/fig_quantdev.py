"""Chart data for Book 17, chapter 19."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_quantdev as a  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
GROUPS = (("quant", ("13-2099.01",)), ("software", ("15-1252",)), ("stats", ("15-2041", "15-2031")),
          ("data", ("15-2051", "15-2051.01")))
LABEL = {"quant researcher": "quantitative researcher", "quant developer": "quant developer",
         "software engineer": "software engineer", "ml and data": "machine learning and data"}
mix, tot = a.soc_mix()
with open(OUT / "soc_mix.csv", "w") as f:
    f.write("pos,family,n," + ",".join(g for g, _ in GROUPS) + ",other\n")
    for i, fam in enumerate(reversed(a.FAMILIES)):
        shares = [sum(mix[fam].get(c, 0) for c in codes) for _, codes in GROUPS]
        other = tot[fam] - sum(shares)
        f.write(f"{i + 1},{LABEL[fam]},{tot[fam]}," + ",".join(f"{100 * x / tot[fam]:.1f}" for x in shares + [other])
                + "\n")
c = a.soc_cells()
with open(OUT / "levels.csv", "w") as f:
    f.write("level,dev,dev_lo,dev_hi,quant,quant_lo,quant_hi\n")
    for j, lv in enumerate(a.LEVELS):
        d, q = c[("15-1252", lv)], c[("13-2099.01", lv)]
        f.write(f"{j + 1},{d['p50'] / 1000:.1f},{d['lo50'] / 1000:.1f},{d['hi50'] / 1000:.1f},"
                f"{q['p50'] / 1000:.1f},{q['lo50'] / 1000:.1f},{q['hi50'] / 1000:.1f}\n")
g = a.gaps()
with open(OUT / "gap.csv", "w") as f:
    f.write("pos,level,d2021,lo2021,hi2021,d2025,lo2025,hi2025\n")
    for j, lv in enumerate(("all",) + a.LEVELS):
        x, y = g[(2021, lv)], g[(2025, lv)]
        f.write(f"{j + 1},{lv}," + ",".join(f"{v / 1000:.2f}" for v in (x["diff"], x["diff_lo"], x["diff_hi"],
                                                                     y["diff"], y["diff_lo"], y["diff_hi"])) + "\n")
m = a.level_mix()
with open(OUT / "level_mix.csv", "w") as f:
    f.write("level,dev,quant\n")
    for j in range(len(a.LEVELS)):
        f.write(f"{j + 1},{100 * m['15-1252'][j]:.1f},{100 * m['13-2099.01'][j]:.1f}\n")
