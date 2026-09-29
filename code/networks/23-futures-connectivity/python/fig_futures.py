"""Chart CSVs of chapter 23: win rate against sessions under the two gateway designs, a bystander's latency when
everyone multiplies, and the monthly value of each extra session against its fee (labelled simulation)."""
import nw_futures as n

OUT = n.ROOT / "figdata" / "networks" / "23-futures-connectivity"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    c = n.curves()
    rows = ["k,solo,everyone,segment,by_solo,by_everyone"]
    for i, k in enumerate(n.K):
        s, e, g = c["solo"][i], c["everyone"][i], c["segment"][i]
        rows.append(f"{k},{s[0]:.4f},{e[0]:.4f},{g[0]:.4f},{s[2]:.3f},{e[2]:.3f}")
    (OUT / "wins.csv").write_text("\n".join(rows) + "\n")
    rows = ["k,value,fee"] + [f"{k},{v:.1f},{n.fee(k):.0f}" for k, v in n.marginal(c["solo"])]
    (OUT / "marginal.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
