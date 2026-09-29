"""Chart CSVs of chapter 29: each venue's achieved latency as a share of its target, and the annual budget by
category; also writes the plan's exported cost table for Book 16 (code/firm/connplan/data/cost_table.csv)."""
import nw_plan as n

OUT = n.ROOT / "figdata" / "networks" / "29-build-a-connectivity-plan"
SHORT = {"NYSE equities (Mahwah)": "NYSE", "CME data (Aurora to Mahwah)": "CME data", "CME orders (Mahwah to Aurora)":
         "CME orders", "Binance (AWS Tokyo)": "Binance"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    r = n.report()
    rows = ["x,venue,share"] + [f"{i},{SHORT[x['venue']]},{100 * x['achieved_us'] / x['target_us']:.1f}"
                                for i, x in enumerate(r["latency"])]
    (OUT / "latency.csv").write_text("\n".join(rows) + "\n")
    by = r["budget"]["by_category"]
    rows = ["x,category,kusd"] + [f"{i},{k},{v / 1000:.1f}" for i, (k, v) in enumerate(by.items())]
    (OUT / "budget.csv").write_text("\n".join(rows) + "\n")
    n.cp.export_cost_table(n.PLAN, n.PRICES, n.ROOT / "code" / "firm" / "connplan" / "data" / "cost_table.csv")


if __name__ == "__main__":
    main()
