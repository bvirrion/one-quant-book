"""Chapter 1 of Book 6: curve construction. An illustrative SOFR curve from deposits, futures and
swaps, built with four interpolations; forward curves, locality of a one-pillar bump, bucketed
DV01 of off-pillar swaps, the swap book of the weekend problem, and the Svensson curve."""
import datetime as dt
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/curvebuild"))
from firm_curvebuild import (  # noqa: E402
    KINDS,
    Deposit,
    Future,
    Swap,
    bucket_sensitivities,
    calibrate,
    imm_date,
    swap_pv,
    with_quote,
)

SPOT = dt.date(2026, 9, 29)
FUT = [(2026, 12), (2027, 3), (2027, 6), (2027, 9)]
FUT_PRICES = [96.50, 96.62, 96.72, 96.78]
FUT_CONVEXITY = [0.00002, 0.00004, 0.00006, 0.00009]     # illustrative, rate units
SWAP_YEARS = [2, 3, 4, 5, 7, 10, 12, 15, 20, 25, 30]
SWAP_RATES = [0.0330, 0.0332, 0.0337, 0.0343, 0.0357, 0.0375, 0.0385, 0.0396, 0.0405, 0.0406, 0.0403]


def instruments():
    out = [Deposit(SPOT, dt.date(2026, 10, 29), 0.0362, "1M"), Deposit(SPOT, dt.date(2026, 12, 29), 0.0358, "3M")]
    starts = [imm_date(y, m) for y, m in FUT] + [imm_date(2027, 12)]
    for k, (p, c) in enumerate(zip(FUT_PRICES, FUT_CONVEXITY, strict=True)):
        out.append(Future(starts[k], starts[k + 1], p, c, f"F{k + 1}"))
    out += [Swap(SPOT, n, r, f"{n}Y") for n, r in zip(SWAP_YEARS, SWAP_RATES, strict=True)]
    return out


def curves() -> dict:
    return {k: calibrate(SPOT, instruments(), k) for k in KINDS}


def forward_table(step: float = 0.1, horizon: float = 30.0) -> list[list[float]]:
    cs = curves()
    rows = []
    for i in range(1, int(round(horizon / step)) + 1):
        t = i * step
        rows.append([t] + [100 * cs[k].curve.fwd_t(t) for k in KINDS])
    return rows


def locality(pillar: str = "7Y", step: float = 0.1, horizon: float = 30.0) -> list[list[float]]:
    """Change in the instantaneous forward curve (bp) when one swap quote rises by 1 bp."""
    ins = instruments()
    k = next(i for i, x in enumerate(ins) if x.label == pillar)
    bumped = list(ins)
    bumped[k] = with_quote(ins[k], ins[k].quote() + 1e-4)
    rows = []
    base = {kd: calibrate(SPOT, ins, kd).curve for kd in KINDS}
    up = {kd: calibrate(SPOT, bumped, kd).curve for kd in KINDS}
    for i in range(1, int(round(horizon / step)) + 1):
        t = i * step
        rows.append([t] + [1e4 * (up[kd].fwd_t(t) - base[kd].fwd_t(t)) for kd in KINDS])
    return rows


BUMP = 1e-6          # bucketed risk: bump each quote by 0.01 bp, then scale to 1 bp (see exercise 7)


def buckets(kind: str, pv, bump: float = BUMP) -> list[float]:
    """Bucketed sensitivity per basis point of each quote (bump, recalibrate, reprice, scale)."""
    return [x * 1e-4 / bump for x in bucket_sensitivities(SPOT, instruments(), kind, pv, bump)]


def off_pillar_buckets(years: int, notional: float = 1e8, bump: float = BUMP) -> dict[str, list[float]]:
    """Bucketed DV01 of a par payer swap of `years`, per interpolation scheme."""
    out = {}
    for kd in KINDS:
        c = calibrate(SPOT, instruments(), kd).curve
        k = Swap(SPOT, years, 0.0).model(c)
        out[kd] = buckets(kd, lambda cv, k=k: swap_pv(cv, SPOT, years, k, notional), bump)
    return out


# ---- the weekend problem: a swap book revalued after an interpolation change ---------------------
BOOK = [(6, 900e6, True), (8, 700e6, False), (9, 600e6, True), (11, 800e6, False), (13, 500e6, True),
        (17, 700e6, False), (22, 800e6, True)]          # (years, notional, payer); 5.0 bn gross


def book_pv(curve, fixed: dict[int, float]) -> float:
    return sum(swap_pv(curve, SPOT, n, fixed[n], q, pay) for n, q, pay in BOOK)


def interpolation_switch(old: str = "linear_zero", new: str = "monotone_convex") -> dict:
    c_old = calibrate(SPOT, instruments(), old).curve
    c_new = calibrate(SPOT, instruments(), new).curve
    fixed = {n: Swap(SPOT, n, 0.0).model(c_old) for n, _, _ in BOOK}   # traded at par on the old curve
    return {"pnl": book_pv(c_new, fixed), "par_old": fixed,
            "par_new": {n: Swap(SPOT, n, 0.0).model(c_new) for n, _, _ in BOOK},
            "buckets_old": buckets(old, lambda c: book_pv(c, fixed)),
            "buckets_new": buckets(new, lambda c: book_pv(c, fixed))}


# ---- Nelson-Siegel and Svensson ---------------------------------------------------------------------
ECB_2026_09_22 = {"b0": 1.6305742011, "b1": 0.6958329015, "b2": 2.5849118333, "b3": 6.6621862503,
                  "tau1": 1.0632472342, "tau2": 14.4455604467}     # ECB AAA curve, per cent (ECB statistics)
ECB_SPOT_2026_09_22 = {1: 2.96792071, 5: 3.2169356314, 10: 3.4527398521, 30: 3.717737327}


def svensson(t: float, b0: float, b1: float, b2: float, b3: float, tau1: float, tau2: float) -> float:
    """Zero rate (same units as the betas), continuous compounding; Nelson-Siegel if b3 = 0."""
    x1, x2 = t / tau1, t / tau2
    l1 = (1 - math.exp(-x1)) / x1
    l2 = (1 - math.exp(-x2)) / x2
    return b0 + b1 * l1 + b2 * (l1 - math.exp(-x1)) + b3 * (l2 - math.exp(-x2))


def svensson_forward(t: float, b0: float, b1: float, b2: float, b3: float, tau1: float, tau2: float) -> float:
    x1, x2 = t / tau1, t / tau2
    return b0 + b1 * math.exp(-x1) + b2 * x1 * math.exp(-x1) + b3 * x2 * math.exp(-x2)


def with_one_year_swap(offset: float = 2e-4, kind: str = "flat_forward"):
    """Put the one-year swap back, quoted `offset` above the rate the futures imply; return the
    implied rate and the recalibrated curve (exercise 3)."""
    c = calibrate(SPOT, instruments(), kind).curve
    k = Swap(SPOT, 1, 0.0).model(c)
    ins = sorted(instruments() + [Swap(SPOT, 1, k + offset, "1Y")], key=lambda i: i.maturity)
    return k, calibrate(SPOT, ins, kind)
