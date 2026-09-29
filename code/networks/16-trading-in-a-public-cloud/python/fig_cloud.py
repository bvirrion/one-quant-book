"""Chart CSVs of chapter 16: simulated round-trip percentiles by case, the naming penalty against the number of
zones, and three monthly plans' costs."""
import nw_cloud as c

OUT = c.ROOT / "figdata" / "networks" / "16-trading-in-a-public-cloud"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    per = {k: c.percentiles(k) for k in c.CASES}
    rows = ["q,pos,same,cross,noisy"]
    for i, q in enumerate(c.QUANTILES):
        rows.append(f"{q},{i},{per['same zone'][q]:.1f},{per['cross zone'][q]:.1f},"
                    f"{per['shared host, noisy neighbour'][q]:.1f}")
    (OUT / "rtt.csv").write_text("\n".join(rows) + "\n")
    (OUT / "penalty.csv").write_text("n,p_same,penalty_us\n" + "".join(f"{n},{p:.4f},{d:.1f}\n"
                                                                      for n, p, d in c.penalty_rows()))
    costs = c.plan_costs()
    rows = ["plan,compute,transfer"] + [f"{k},{v['compute']:.2f},{v['transfer']:.2f}" for k, v in costs.items()]
    (OUT / "plans.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
