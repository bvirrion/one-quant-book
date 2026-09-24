"""Chart data for Chapter 24 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from auction_demo import BOOK, OPRA_PROJECTIONS, compare_rules, simulate_auctions

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/24-options-market-structure"
OUT.mkdir(parents=True, exist_ok=True)

res = compare_rules(115)
with open(OUT / "rules.csv", "w") as f:
    f.write("order,pro_rata,customer,entitled\n")
    for q in BOOK:
        f.write(f"{q.oid}," + ",".join(str(res[k].get(q.oid, 0)) for k in ("pro_rata", "customer", "entitled")) + "\n")

with open(OUT / "auction.csv", "w") as f:
    f.write("p_improve,share_1,share_3,improved_1,improved_3\n")
    for k in range(0, 11):
        p = k / 10
        s1, i1 = simulate_auctions(4000, 1.0, p, 24)
        s3, i3 = simulate_auctions(4000, 3.0, p, 24)
        f.write(f"{p:.1f},{s1 * 100:.1f},{s3 * 100:.1f},{i1 * 100:.1f},{i3 * 100:.1f}\n")

with open(OUT / "opra.csv", "w") as f:
    f.write("date,messages_bn_day,peak_m_per_100ms\n")
    f.writelines(f"{d},{m},{p}\n" for d, m, p in OPRA_PROJECTIONS)
