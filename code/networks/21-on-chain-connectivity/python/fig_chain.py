"""Chart CSVs of chapter 21: the share of nodes reached against time, flooding and square-root fan-out; arrival
at a leader through gossip and through the nearest block engine, by city; and the share of leaders reached in time
against the deadline (labelled simulation)."""
import nw_chain as n

OUT = n.ROOT / "figdata" / "networks" / "21-on-chain-connectivity"
LABEL = {"amsterdam": "Amsterdam", "dublin": "Dublin", "frankfurt": "Frankfurt", "london": "London", "ny": "New York",
         "slc": "Salt Lake City", "singapore": "Singapore", "tokyo": "Tokyo"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ["city,gossip,direct"]
    for c in n.CITIES:
        r = n.to_leader(c)
        rows.append(f"{LABEL[c]},{r['gossip']:.2f},{r['direct']:.2f}")
    (OUT / "leaders.csv").write_text("\n".join(rows) + "\n")
    rows = ["deadline,gossip,direct"] + [f"{d},{g:.4f},{x:.4f}" for d, g, x in n.timely_rates()]
    (OUT / "timely.csv").write_text("\n".join(rows) + "\n")
    arr = {m: sorted(n.cn.spread(n.GRAPH, n.SOURCE, m)) for m in ("flood", "sqrt")}
    rows = ["ms,flood,sqrt"]
    for t in range(0, 181, 2):
        f, q = (sum(a <= t for a in arr[m]) / len(arr[m]) for m in ("flood", "sqrt"))
        rows.append(f"{t},{f:.4f},{q:.4f}")
    (OUT / "propagation.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
