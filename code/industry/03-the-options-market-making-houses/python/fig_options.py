"""Chart data for Book 17, chapter 3 (deterministic, from the committed tables)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_options as o  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "results.csv", "w") as f:
    f.write("year,nti,profit,equity\n")
    for r in o.results():
        f.write(f"{int(r['year'])},{r['net_trading_income'] / 1000:.3f},{r['net_profit'] / 1000:.3f},"
                f"{r['total_equity'] / 1000:.3f}\n")

q = ("p10", "p25", "p50", "p75", "p90")
pay = o.options_pay()
with open(OUT / "options_pay.csv", "w") as f:
    f.write("pos,label," + ",".join(q) + "\n")
    pos = 0
    for role, lab in (("trader", "traders"), ("software engineer", "software engineers"),
                      ("quant researcher", "researchers"), ("all", "all titles")):
        for grp, g in (("other market makers", "other"), ("options houses", "options houses")):
            pos += 1
            c = pay[(role, grp)]
            f.write(f"{pos},{lab}; {g}," + ",".join(f"{c[k] / 1000:.1f}" for k in q) + "\n")
