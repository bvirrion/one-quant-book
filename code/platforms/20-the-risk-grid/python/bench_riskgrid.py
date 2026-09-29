"""Chapter 20 measured data (not a fig_*.py): the cost of one pricing call per kind of trade with the real library
(Book 6's swaps and swaptions, Book 5's equity options and Monte Carlo autocallables at the library's 100,000 paths),
and the cost of swap pillar deltas by bumping (sixteen repricings) and by one adjoint sweep of Book 4's tape. Best of
three batches, one thread. Writes measured_costs.csv (+ .meta)."""
import datetime as dt
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
for p in ("code/firm/ubench", "code/firm/riskengine", "code/firm/pricing", "code/firm/riskgrid"):
    sys.path.insert(0, str(ROOT / p))
import firm_riskengine as RE  # noqa: E402
import firm_riskgrid as G  # noqa: E402
import firm_ubench as u  # noqa: E402

fp = RE.fp
OUT = ROOT / "figdata/platforms/20-the-risk-grid"
ASOF = dt.date(2026, 9, 28)
CURVE = RE.PillarCurve(ASOF, (0.030, 0.031, 0.032, 0.033, 0.034, 0.035, 0.036, 0.036))
MD = fp.MarketData(ASOF, {"SPX": 5000.0, "SOFR": 0.0}, {"USD": CURVE},
                   vols={"SPX": fp.FlatVol(0.2), "SOFR": fp.FlatVol(0.01)})
SWAP = RE.IRSwap(id="S", underlying="SOFR", currency="USD", years=10, fixed=0.034)
INSTRUMENTS = {
    "swap": (SWAP, None, 300),
    "swaption": (RE.Swaption(id="SO", underlying="SOFR", currency="USD", expiry=ASOF + dt.timedelta(days=365),
                             tenor=5, strike=0.034), None, 300),
    "option": (fp.EuropeanOption(id="EO", underlying="SPX", currency="USD", strike=5000.0,
                                 expiry=ASOF + dt.timedelta(days=180), right="C"), None, 300),
    "autocallable": (fp.Autocallable(id="AC", underlying="SPX", currency="USD", underlyings=("SPX",), initial=(5000.0,),
                                     obs_dates=tuple(ASOF + dt.timedelta(days=182 * (i + 1)) for i in range(6)),
                                     coupon=4.0, notional=100.0), fp.MonteCarloEngine(), 5),
}


def best(fn, n, reps=3):
    b = float("inf")
    for _ in range(reps):
        t = time.perf_counter()
        for _ in range(n):
            fn()
        b = min(b, (time.perf_counter() - t) / n)
    return b


def main():
    rows = []
    for kind, (inst, eng, n) in INSTRUMENTS.items():
        m = RE.model_for(inst)
        rows.append([kind, f"{best(lambda i=inst, m=m, e=eng: fp.price(i, MD, m, e), n):.7f}"])
    factors = [f"CURVE:USD:{p}" for p in RE.PILLARS]
    bump = best(lambda: fp.sensitivities(SWAP, MD, factors, RE.model_for(SWAP)), 50)
    adjoint = best(lambda: G.swap_pv_adjoint(CURVE.zeros, RE.TENORS, 10, 0.034), 50)
    rows += [["swap deltas by bump", f"{bump:.7f}"], ["swap deltas by adjoint", f"{adjoint:.7f}"]]
    u.write_measured(OUT / "measured_costs.csv", ["kind", "seconds"], rows,
                     source="code/platforms/20-the-risk-grid/python/bench_riskgrid.py",
                     timer="best of 3 batches, time.perf_counter per call, one thread")


if __name__ == "__main__":
    main()
