"""Chart CSVs of chapter 19: Tokyo's hubs against their floors, the p99 gain of racing routes against their
correlation, and the duplicates a venue accepts against the first copy's fill time (labelled simulations)."""
import nw_race as n

OUT = n.ROOT / "figdata" / "networks" / "19-cross-region-crypto-networks"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ["hub,fibre_floor,specialist,backbone"]
    for r in n.hub_rows():
        if "backbone" in r:
            rows.append(f"{n.NAMES[r['hub']]},{r['fib_rtt']:.1f},{r['specialist']:.1f},{r['backbone']:.1f}")
    (OUT / "hubs.csv").write_text("\n".join(rows) + "\n")
    rows = ["rho,two,three"] + [f"{rho},{a:.1f},{b:.1f}" for rho, a, b in n.race_rows((0.0, 0.1, 0.2, 0.3, 0.4, 0.5,
                                                                                     0.6, 0.7, 0.8, 0.9))]
    (OUT / "race.csv").write_text("\n".join(rows) + "\n")
    rows = ["fill_us,accepted"] + [f"{f},{a:.3f}" for f, a in n.duplicate_rows((0, 250, 500, 1000, 1500, 2000, 3000,
                                                                                4000, 6000, 8000))]
    (OUT / "dups.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
