"""Chart data for Book 17, chapter 14 (reads the derived tables)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_paylevels as a  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
rg = a.ranges()
LABEL = {"systematic fund": "systematic fund", "multi-manager platform": "platform", "market maker": "market maker",
         "bank": "bank", "exchange": "exchange"}


def row(k):
    c = rg.get(k)
    if not c or c["suppressed"]:
        return "nan,nan,nan"
    return f"{c['p50'] / 1000:.1f},{(c['p75'] - c['p50']) / 1000:.1f},{(c['p50'] - c['p25']) / 1000:.1f}"


with open(OUT / "base_by_kind.csv", "w") as f:
    f.write("pos,kind,all,all_up,all_dn,qr,qr_up,qr_dn,se,se_up,se_dn\n")
    for i, kind in enumerate(a.KINDS):
        cells = ",".join(row((2025, kind, r, "all")) for r in ("all", "quant researcher", "software engineer"))
        f.write(f"{i + 1},{LABEL[kind]},{cells}\n")

with open(OUT / "base_by_level.csv", "w") as f:
    f.write("level,bank,market_maker,systematic_fund,exchange\n")
    for j, lvl in enumerate(("I", "II", "III", "IV")):
        vals = []
        for kind in ("bank", "market maker", "systematic fund", "exchange"):
            c = rg.get((2025, kind, "all", lvl))
            vals.append("nan" if not c or c["suppressed"] else f"{c['p50'] / 1000:.1f}")
        f.write(f"{j + 1}," + ",".join(vals) + "\n")

imp = a.implied_ratios()
mm, bank = rg[(2025, "market maker", "all", "all")], rg[(2025, "bank", "all", "all")]
eba = a.eba()
fx = a.eur_usd(2025)
with open(OUT / "slices.csv", "w") as f:
    f.write("pos,slice,lo,hi\n")
    f.write(f"1,bank offered base (IQR),{bank['p25'] / 1000:.0f},{bank['p75'] / 1000:.0f}\n")
    f.write(f"2,market maker offered base (IQR),{mm['p25'] / 1000:.0f},{mm['p75'] / 1000:.0f}\n")
    f.write(f"3,bank staff cost per head,{imp['bank']['lo'] / 1000:.0f},{imp['bank']['hi'] / 1000:.0f}\n")
    lo, hi = imp["market maker"]["lo"] / 1000, imp["market maker"]["hi"] / 1000
    f.write(f"4,market maker staff cost per head,{lo:.0f},{hi:.0f}\n")
    ib = float(eba[("credit institutions", "Investment banking")]["avg_total_eur"]) * fx / 1000
    oa = float(eba[("investment firms", "Dealing on own account")]["avg_total_eur"]) * fx / 1000
    f.write(f"5,EU bank investment banking high earners (mean),{ib:.0f},{ib:.0f}\n")
    f.write(f"6,EU dealing on own account high earners (mean),{oa:.0f},{oa:.0f}\n")
