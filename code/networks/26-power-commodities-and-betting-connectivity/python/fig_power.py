"""Chart CSV of chapter 26: our share of scarce cross-border capacity against our latency to the shared order book,
when one order's worth or three orders' worth of capacity is left (labelled simulation)."""
import nw_power as n

OUT = n.ROOT / "figdata" / "networks" / "26-power-commodities-and-betting-connectivity"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    one, three = n.share_curve(1), n.share_curve(3)
    rows = ["latency_ms,one,three"] + [f"{m},{a:.4f},{b:.4f}" for m, a, b in zip(n.GRID, one, three, strict=True)]
    (OUT / "race.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
