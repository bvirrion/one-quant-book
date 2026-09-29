"""Chart CSVs of chapter 15: expected downtime against annual cost for three designs, and the distribution of a
simulated year's downtime (a labelled simulation)."""
import numpy as np
import nw_buy as b

OUT = b.ROOT / "figdata" / "networks" / "15-buying-connectivity"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    res = b.results()
    rows = ["design,cost_k,expected_min,loss_k"]
    for k, v in res.items():
        rows.append(f"{k},{v['annual_cost'] / 1000:.1f},{max(v['expected_min'], 0.01):.3f},{v['loss'] / 1000:.2f}")
    (OUT / "designs.csv").write_text("\n".join(rows) + "\n")
    for d, slug in zip(b.designs(), ("single", "duct", "diverse"), strict=True):
        sims = np.sort([b.sm.simulate_year(d, seed=k, sigma=b.ASSUME["sigma"])["down_min"] for k in range(1000)])
        pts = [(q, float(np.quantile(sims, q / 100))) for q in range(0, 101, 5)]
        (OUT / f"ecdf_{slug}.csv").write_text("pct,minutes\n" + "".join(f"{q},{max(m, 0.01):.3f}\n" for q, m in pts))


if __name__ == "__main__":
    main()
