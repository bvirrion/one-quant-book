"""Chart data for Book 12, chapter 29: net P&L per session and mark-outs against the decision latency."""
import pathlib

import ml_lobmodel as m

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "ml" / "29-build-an-order-book-model-end-to-end"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, base = m.latency_table()
    with open(OUT / "latency.csv", "w") as f:
        f.write("ms,pnl,lo,hi,mo1,mo01,stale,base\n")
        for r in rows:
            if r["latency ms"] == 0:
                continue                                                # a log axis: 0 equals the 150 ns row
            f.write(f"{r['latency ms']:.6g},{r['pnl']:.2f},{r['pnl'] - r['se']:.2f},{r['pnl'] + r['se']:.2f},"
                    f"{r['markout 1 s']:.3f},{r['markout 0.1 s']:.3f},{r['staleness ms']:.4g},{base['pnl']:.2f}\n")


if __name__ == "__main__":
    main()
