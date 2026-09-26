"""Chapter 26 measured data (not a fig_*.py): ten live runs of the assembled path (firm.ticktotrade) on the loopback
interface, four pinned threads, the recorded line replayed at 20 times its recorded spacing. Outputs measured_stages.csv
(per stage and end to end: median, 99th and 99.9th percentiles, and the number of orders), measured_t2t_ccdf.csv
(the tick-to-trade and in-process distributions as complementary cumulative points) and measured_budget.csv (chapter
1's budget checked with firm.latbudget)."""
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
sys.path.insert(0, str(HERE))
import firm_ubench as u  # noqa: E402
import ll_t2t as L  # noqa: E402

OUT = ROOT / "figdata/low-latency/26-build-tick-to-trade-measured"
SRC = "code/low-latency/26-build-tick-to-trade-measured/cpp/ll_t2t_run.cpp"
LINE = ROOT / "code/firm/ticktotrade/data/line.bin"
RUNS, STRETCH, CPUS = 10, 20, (2, 4, 6, 8)


def main():
    exe = u.compile_cpp(ROOT / SRC, flags=(*u.DEFAULT, "-pthread"), includes=[ROOT / "code/firm/ticktotrade/cpp"])
    rows, hashes, allocs = [], set(), []
    for _ in range(RUNS):
        for line in u.run(exe, LINE, STRETCH, *CPUS).splitlines():
            f = line.split(",")
            if f[0] == "o":
                rows.append(dict(zip(("kind", "nth", *L.STAMPS), f[1:], strict=True)))
            elif f[0] == "summary":
                hashes.add(f[3])
                allocs.append(int(f[4]))
    s = L.stage_samples(rows)
    out = []
    for name, v in s.items():
        q = np.quantile(v, [0.5, 0.99, 0.999], method="inverted_cdf")
        out.append([name, f"{q[0]:.0f}", f"{q[1]:.0f}", f"{q[2]:.0f}", len(v)])
    meta = dict(source=SRC, runs=RUNS, stretch=STRETCH, cpus="exchange 2, feed 4, engine 6, venue 8",
                order_hashes=" ".join(sorted(hashes)), allocations_after_warmup=" ".join(map(str, allocs)),
                path="UDP loopback in (lines A and B), feed handler, ring, engine, risk gate, gateway, TCP out")
    u.write_measured(OUT / "measured_stages.csv", ["stage", "p50_ns", "p99_ns", "p999_ns", "n"], out, **meta)
    ccdf = []
    for name in ("tick to trade", "in process"):
        v = np.sort(s[name])
        for k in range(0, 61):
            p = 1 - 10 ** (-k / 20)                        # 0 to 0.999 in log steps of the tail
            ccdf.append([name.replace(" ", "_"), f"{1 - p:.6f}", f"{np.quantile(v, p, method='inverted_cdf'):.0f}"])
    u.write_measured(OUT / "measured_t2t_ccdf.csv", ["series", "ccdf", "ns"], ccdf, **meta)
    rep = L.budget().check({k: s[k] for k in [st[0] for st in L.STAGES]})
    u.write_measured(OUT / "measured_budget.csv", ["stage", "level", "target_ns", "measured_ns", "ok"],
                     [[r["stage"], r["level"], r["target"], f"{r['measured']:.0f}", r["ok"]] for r in rep], **meta)


if __name__ == "__main__":
    main()
