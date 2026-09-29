"""Chart data for Book 17, chapter 17."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_researcher as a  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
LABEL = {"systematic fund": "systematic fund", "multi-manager platform": "platform", "market maker": "market maker",
         "bank": "bank", "exchange": "exchange"}
q = ("p10", "p25", "p50", "p75", "p90")
p = a.pay()
with open(OUT / "pay_kind.csv", "w") as f:
    f.write("pos,kind," + ",".join(q) + "\n")
    for i, k in enumerate(reversed(a.KINDS)):
        c = p["all"][k]
        f.write(f"{i + 1},{LABEL[k]}," + ",".join(f"{c[x] / 1000:.1f}" for x in q) + "\n")
with open(OUT / "levels.csv", "w") as f:
    f.write("level,market_maker,bank,systematic_fund\n")
    for j, lvl in enumerate(("I", "II", "III", "IV")):
        vals = []
        for k in ("market maker", "bank", "systematic fund"):
            c = p[lvl].get(k)
            vals.append("nan" if not c or c["suppressed"] else f"{c['p50'] / 1000:.1f}")
        f.write(f"{j + 1}," + ",".join(vals) + "\n")
with open(OUT / "feedback.csv", "w") as f:
    f.write("horizon,days,sr,years\n")
    for h, ppy, sr, years, _ in a.law_curve():
        f.write(f"{h},{252 / ppy:.5f},{sr:.3f},{years:.5f}\n")
with open(OUT / "named.csv", "w") as f:
    f.write("horizon,days,years\n")
    for h, (_sr, years, _) in a.named().items():
        f.write(f"{h},{252 / a.HORIZONS[h]:.5f},{years:.4f}\n")
