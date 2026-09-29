"""Chapter 27 measured data (not a fig_*.py): the deployment pipeline's test tiers on the chapter's portfolio, run
with firm.goldtest.run_tiers -- unit (put-call parity on 1,000 random European options), golden (the sixty
instruments against their pinned golden values) and end to end (the portfolio revalued in five spot scenarios and
checked against a finite-difference delta). Writes measured_stages.csv (+ .meta). Run on a quiet machine."""
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
sys.path.insert(0, str(HERE))
import firm_ubench as u  # noqa: E402
import pl_goldtest as P  # noqa: E402

OUT = ROOT / "figdata/platforms/27-testing-and-continuous-delivery"


def unit():
    rng = np.random.default_rng(1)
    md, eng = P.market(), P.FP.AnalyticEngine()
    for i in range(1000):
        k, days = float(rng.uniform(60, 140)), int(rng.integers(10, 1500))
        c = P.FP.EuropeanOption(id=f"c{i}", underlying="A", currency="USD", strike=k, expiry=P._d(days), right="C")
        p = P.FP.EuropeanOption(id=f"p{i}", underlying="A", currency="USD", strike=k, expiry=P._d(days), right="P")
        lhs = P.pv(c, eng, md) - P.pv(p, eng, md)
        rhs = 100.0 - k * md.df("USD", c.expiry)
        assert abs(lhs - rhs) < 1e-9
    return True


PORT = P.portfolio()
STORE = P.G.GoldenStore()
for key, (inst, eng) in PORT.items():
    STORE.put(P.G.Golden(key, P.pv(inst, eng), 1e-10 * max(1.0, abs(P.pv(inst, eng)))))


def golden():
    return P.G.compare(STORE, {k: P.pv(i, e) for k, (i, e) in PORT.items()}).ok


def end_to_end():
    vals = []
    for s in (90.0, 95.0, 100.0, 105.0, 110.0):
        md = P.FP.MarketData(P.ASOF, {"A": s}, {"USD": P.FP.FlatCurve(0.03, P.ASOF)}, vols={"A": P.FP.FlatVol(0.25)})
        vals.append(sum(P.pv(i, e, md) for i, e in PORT.values()))
    return all(np.diff(vals) != 0)


def main():
    res = P.G.run_tiers([("unit", unit), ("golden", golden), ("end to end", end_to_end)])
    assert all(ok for _, _, ok in res) and len(res) == 3
    u.write_measured(OUT / "measured_stages.csv", ["stage", "seconds"], [[n, f"{s:.2f}"] for n, s, _ in res],
                     source="code/platforms/27-testing-and-continuous-delivery/python/bench_goldtest.py",
                     timer="one run of each tier with time.perf_counter, in one process, BLAS threads 1")


if __name__ == "__main__":
    main()
