"""Chapter 12 of Book 6: mortgage modelling. A pass-through pool (WAC 6.0%, coupon 5.5%, 29 years left)
priced by option-adjusted spread on chapter 1's SOFR curve with Hull-White paths (kappa 3%, sigma 90 bp),
a turnover-plus-refinancing prepayment model with burnout, IO/PO strips, effective duration and
convexity, and the extension of duration after a 100 bp rise (the 2003 convexity event)."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
for p in ("code/firm/mbsoas", "code/rates-credit-risk/01-curve-construction/python"):
    sys.path.insert(0, str(ROOT / p))
import rc_curves as rc  # noqa: E402
from firm_mbsoas import Pool, PrepayModel, analyse, pool_flows, pv_paths, s_curve_table, simulate_paths  # noqa: E402

CURVE = rc.curves()["monotone_convex"].curve
POOL = Pool()
MODEL = PrepayModel()
PRICE = 100.0
KAPPA, SIGMA, PATHS = 0.03, 0.009, 4000


def base() -> dict:
    return analyse(CURVE, POOL, MODEL, PRICE, KAPPA, SIGMA, PATHS)


def value_at(shift: float, oas: float, model: PrepayModel = MODEL) -> float:
    months = POOL.term - POOL.age
    rs, p10 = simulate_paths(CURVE, KAPPA, SIGMA, months, PATHS, 17, shift=shift)
    io, po = pool_flows(POOL, model, p10)
    return float(pv_paths(io + po, rs, oas).mean())


def duration_at(shift: float, oas: float, dy: float = 0.0025) -> dict:
    v0, dn, up = value_at(shift, oas), value_at(shift - dy, oas), value_at(shift + dy, oas)
    return {"value": v0, "duration": (dn - up) / (2 * v0 * dy), "convexity": (dn + up - 2 * v0) / (v0 * dy * dy)}


def price_rate_table(oas: float) -> list[tuple[float, float]]:
    """Pool value against a parallel shift of the curve (bp), OAS held."""
    return [(s, value_at(s * 1e-4, oas)) for s in range(-200, 201, 25)]


def no_burnout(oas: float) -> float:
    m = PrepayModel(burnout=0.0)
    return value_at(0.0, oas, m)


def s_curve():
    return s_curve_table(MODEL)


def io_po_table(oas: float) -> list[tuple[int, float, float]]:
    months = POOL.term - POOL.age
    out = []
    for s in range(-200, 201, 50):
        rs, p10 = simulate_paths(CURVE, KAPPA, SIGMA, months, PATHS, 17, shift=s * 1e-4)
        io, po = pool_flows(POOL, MODEL, p10)
        out.append((s, float(pv_paths(io, rs, oas).mean()), float(pv_paths(po, rs, oas).mean())))
    return out


def swap10_dv01(shift: float, notional: float = 1e9) -> float:
    """DV01 (currency per bp) of a ten-year par OIS swap on chapter 1's curve shifted in parallel."""
    sys.path.insert(0, str(ROOT / "code/firm/curve"))
    from firm_curve import annuity, schedule
    c = CURVE.bumped(None, shift)
    return notional * annuity(c, schedule(rc.SPOT, 10)) * 1e-4


def convexity_event(face: float = 10e9) -> dict:
    """A holder of `face` of the pool, hedged to zero DV01 with ten-year payer swaps: rates rise 100 bp."""
    b = base()
    d0, d1 = duration_at(0.0, b["oas"]), duration_at(0.01, b["oas"])
    dv0 = d0["duration"] * d0["value"] / 100 * face * 1e-4
    dv1 = d1["duration"] * d1["value"] / 100 * face * 1e-4
    extra = dv1 - dv0
    return {"dv01_before": dv0, "dv01_after": dv1, "extra": extra, "swap_dv01": swap10_dv01(0.01),
            "notional": extra / swap10_dv01(0.01) * 1e9, "d0": d0, "d1": d1}
