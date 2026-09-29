"""Chart CSVs of chapter 20: stale symbol-seconds by recovery design, the venue-clock estimate against the truth,
and the rate budget's split (labelled simulations)."""
import nw_api as a

OUT = a.ROOT / "figdata" / "networks" / "20-api-engineering-for-crypto-venues"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ["case,per_symbol,per_conn"]
    for r in a.resync_rows((5,)):
        rows.append(f"{r['depth']},{r['per_symbol_s']:.2f},{r['per_conn_s']:.2f}")
    (OUT / "staleness.csv").write_text("\n".join(rows) + "\n")
    est, true = a.skew_series()
    pairs = zip(est, true, strict=True)
    rows = ["minute,estimate,truth"] + [f"{t / 60000:.1f},{e:.4f},{v:.4f}" for (t, e), (_, v) in pairs]
    (OUT / "skew.csv").write_text("\n".join(rows) + "\n")
    rows = ["strategy,demand,share"]
    demands = {"market making": 4000, "arbitrage": 3000, "risk": 500}
    for k, v in a.budget().items():
        rows.append(f"{k},{demands[k]},{v:.0f}")
    (OUT / "budget.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
