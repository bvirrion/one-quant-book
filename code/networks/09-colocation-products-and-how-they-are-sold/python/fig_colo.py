"""Chart CSV of chapter 9: annual cost of each footprint, recurring against amortised one-time fees."""
import nw_colo as c

OUT = c.ROOT / "figdata" / "networks" / "09-colocation-products-and-how-they-are-sold"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ["footprint,recurring_k,one_time_k"]
    for k, b in c.bills().items():
        rows.append(f"{k},{12 * b['monthly'] / 1000:.1f},{12 * b['amortised'] / 1000:.1f}")
    (OUT / "bills.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
