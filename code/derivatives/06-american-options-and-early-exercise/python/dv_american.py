"""American options and early exercise: premium, boundary, dividends, Bermudans (Book 5, Chapter 6)."""
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
for comp in ("bs", "binomial", "american"):
    sys.path.insert(0, str(ROOT / f"code/firm/{comp}"))
from firm_american import baw, bermudan_put, dividend_threshold, exercise_decision, put_boundary  # noqa: E402
from firm_binomial import price as tree  # noqa: E402
from firm_bs import bs  # noqa: E402

REF = {"spot": 100.0, "strike": 100.0, "t": 1.0, "r": 0.05, "vol": 0.20}
HOOK = {"spot": 100.30, "strike": 80.0, "div": 1.00, "t_left": 29 / 365, "r": 0.04, "vol": 0.25}


def perpetual_put(strike: float, r: float, vol: float) -> tuple[float, float]:
    """Perpetual American put: boundary K g/(1+g) with g = 2r/sigma^2, and its value at the boundary."""
    g = 2 * r / (vol * vol)
    s_star = strike * g / (1 + g)
    return s_star, strike - s_star


def perpetual_put_value(spot: float, strike: float, r: float, vol: float) -> float:
    g = 2 * r / (vol * vol)
    s_star, _ = perpetual_put(strike, r, vol)
    return strike - spot if spot <= s_star else (strike - s_star) * (spot / s_star) ** (-g)


def premium_vs_rate(rates) -> list[tuple[float, float, float]]:
    out = []
    for r in rates:
        am = tree(100, 100, 1.0, r, 0.2, 1001, "P", american=True, method="lr")
        eu = bs(100, 100, 1.0, r, 0.0, 0.2, "P")
        out.append((r, am, am - eu))
    return out


def accuracy_table() -> list[dict]:
    rows = []
    for s, k, t, r, q, v in [(100, 100, 1, 0.05, 0.0, 0.2), (90, 100, 0.5, 0.08, 0.0, 0.3),
                             (110, 100, 0.25, 0.03, 0.0, 0.25), (100, 100, 1, 0.05, 0.04, 0.25)]:
        for right in ("P", "C"):
            b, _ = baw(s, k, t, r, q, v, right)
            tr = tree(s, k, t, r, v, 2001, right, american=True, q=q, method="lr")
            eu = bs(s, k, t, r, q, v, right)
            rows.append({"spot": s, "t": t, "r": r, "q": q, "vol": v, "right": right, "baw": b, "tree": tr,
                         "european": eu, "err": b - tr})
    return rows


def hook() -> dict:
    h = HOOK
    dec = exercise_decision(h["spot"], h["strike"], h["div"], h["t_left"], h["r"], h["vol"])
    d_star = dividend_threshold(h["spot"], h["strike"], h["t_left"], h["r"], h["vol"])
    interest = h["strike"] * (1 - math.exp(-h["r"] * h["t_left"]))
    loss = dec["exercise"] - dec["hold"]
    return {**dec, "d_star": d_star, "interest": interest, "loss_per_share": loss,
            "transfer_usd": loss * 100 * 10_000 * 0.45, "transfer_usd_all": loss * 100 * 10_000}


def boundary_today(c: dict = REF, n: int = 1001) -> float:
    """Today's critical spot: the highest spot at which the American put equals its exercise value."""
    lo, hi = 0.5 * c["strike"], c["strike"]
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        am = tree(mid, c["strike"], c["t"], c["r"], c["vol"], n, "P", american=True, method="lr")
        if am - (c["strike"] - mid) > 1e-9:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def results() -> dict:
    c = REF
    am = tree(c["spot"], c["strike"], c["t"], c["r"], c["vol"], 2001, "P", american=True, method="lr")
    eu = bs(c["spot"], c["strike"], c["t"], c["r"], 0.0, c["vol"], "P")
    bd = put_boundary(c["strike"], c["t"], c["r"], 0.0, c["vol"])
    s_star, _ = perpetual_put(c["strike"], c["r"], c["vol"])
    berm = {m: bermudan_put(c["spot"], c["strike"], c["t"], c["r"], c["vol"], m) for m in (1, 2, 4, 12, 50)}
    return {"american": am, "european": eu, "premium": am - eu, "boundary_1y": boundary_today(),
            "boundary_near": bd[-1][1], "perpetual": s_star,
            "baw": baw(c["spot"], c["strike"], c["t"], c["r"], 0.0, c["vol"], "P")[0],
            "baw_crit": baw(c["spot"], c["strike"], c["t"], c["r"], 0.0, c["vol"], "P")[1], "bermudan": berm}
