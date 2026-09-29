"""Chart CSVs of chapter 7: wire-to-wire quantiles of the software and hardware paths, and the probability of
beating one competitor as a function of the competitor's median latency (model race)."""
import numpy as np
import nw_hwtrade as h

OUT = h.ROOT / "figdata" / "networks" / "07-programmable-hardware-ii-trading-designs"
MEDIANS = (300, 500, 700, 1000, 1500, 2000, 3000, 5000, 7000, 10000)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    p = h.paths()
    q = (0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99, 0.999)
    rows = ["q,software_us,hardware_us"] + [f"{x},{np.quantile(p['software'], x) / 1e3:.3f},"
                                           f"{np.quantile(p['hardware'], x) / 1e3:.3f}" for x in q]
    (OUT / "paths.csv").write_text("\n".join(rows) + "\n")
    rows = ["median_ns,software,hardware"] + [f"{m},{h.win_probability(p['software'], m):.4f},"
                                             f"{h.win_probability(p['hardware'], m):.4f}" for m in MEDIANS]
    (OUT / "race.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
