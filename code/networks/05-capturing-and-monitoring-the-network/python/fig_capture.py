"""Chart CSVs of chapter 5: the wire-to-wire budget by stage (firm.wirepath) and the distribution of wire-to-wire
latency measured from the simulated capture."""
import numpy as np
import nw_capture as c

OUT = c.ROOT / "figdata" / "networks" / "05-capturing-and-monitoring-the-network"
EDGES = np.round(np.logspace(np.log10(2_000), np.log10(100_000), 31)).astype(int)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ["stage,kind,p50_ns,p99_ns"]
    rows += [f"{r['stage']},{r['kind']},{r['p50']:.0f},{r['p99']:.0f}" for r in c.budget_rows()]
    (OUT / "budget.csv").write_text("\n".join(rows) + "\n")
    rec, _ = c.session()
    a = c.analyse(rec)
    h, _ = np.histogram(a["w2w"], bins=EDGES)
    mid = np.sqrt(EDGES[:-1] * EDGES[1:]) / 1000
    rows = ["mid_us,share"] + [f"{m:.3f},{x / len(a['w2w']):.5f}" for m, x in zip(mid, h, strict=True)]
    (OUT / "w2w_hist.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
