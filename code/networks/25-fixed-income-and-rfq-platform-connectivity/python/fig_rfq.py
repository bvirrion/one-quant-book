"""Chart CSVs of chapter 25: our win rate against the pricing stage's median under three client rules, and the chance
of missing the quote timer against its length (labelled simulation)."""
import nw_rfq as n

OUT = n.ROOT / "figdata" / "networks" / "25-fixed-income-and-rfq-platform-connectivity"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    c = n.curves()
    rows = ["pricing_ms,expiry,first_k,first_ok"] + [f"{m:.3f},{a:.4f},{b:.4f},{d:.4f}" for m, a, b, d in
                                                     zip(n.GRID, c["expiry"], c["first_k"], c["first_ok"], strict=True)]
    (OUT / "wins.csv").write_text("\n".join(rows) + "\n")
    m = n.miss_curves()
    rows = ["timer_ms,ours,auto"] + [f"{t:.1f},{a:.6f},{b:.6f}" for t, a, b in zip(n.TIMERS, m["ours"], m["auto"],
                                                                                    strict=True)]
    (OUT / "miss.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
