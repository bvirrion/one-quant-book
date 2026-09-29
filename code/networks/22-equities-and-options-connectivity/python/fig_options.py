"""Chart CSVs of chapter 22: the simulated busy minute around its busiest millisecond, the 10 Gb/s and 25 Gb/s links
needed against the planning percentile, and the time to refresh every quote against the risk layer's latency."""
import numpy as np
import nw_options as n

OUT = n.ROOT / "figdata" / "networks" / "22-equities-and-options-connectivity"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g = n.LINES_GBPS.sum(axis=1)
    k = int(np.argmax(g))
    lo, hi = max(0, k - 300), min(len(g), k + 300)
    ma = np.convolve(g, np.ones(10) / 10, mode="same")
    rows = ["t_ms,gbps_1ms,gbps_10ms"] + [f"{t - k},{g[t]:.2f},{ma[t]:.2f}" for t in range(lo, hi)]
    (OUT / "burst.csv").write_text("\n".join(rows) + "\n")
    ten, twenty_five = n.links_table(), n.links_table(link_gbps=25.0)
    rows = ["x,pct,links10,links25"] + [f"{i},{p},{a},{b}" for i, ((p, a), (_, b)) in enumerate(zip(ten, twenty_five,
                                                                                                  strict=True))]
    (OUT / "links.csv").write_text("\n".join(rows) + "\n")
    one, two = n.refresh_curve(1), n.refresh_curve(2)
    rows = ["risk_us,one_port,two_ports"] + [f"{r},{a:.3f},{b:.3f}" for (r, a), (_, b) in zip(one, two, strict=True)]
    (OUT / "refresh.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
