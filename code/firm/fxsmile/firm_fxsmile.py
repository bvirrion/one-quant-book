"""FX option conventions: deltas, at-the-money strikes, smiles from broker quotes, and a knock-out's
delta at its barrier (build of Book 2, Chapter 19).

S is the spot of BASEQUOTE (quote units per base unit); rd is the quote (domestic) currency's rate,
rf the base (foreign) currency's, both continuously compounded; T in years. A call is a call on the
base currency. phi = +1 for calls, -1 for puts.
"""
import math

N = lambda x: 0.5 * math.erfc(-x / math.sqrt(2.0))                     # noqa: E731


def n_inv(p: float) -> float:
    lo, hi = -10.0, 10.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if N(mid) < p else (lo, mid)
    return 0.5 * (lo + hi)


def forward(s: float, t: float, rd: float, rf: float) -> float:
    return s * math.exp((rd - rf) * t)


def gk(s: float, k: float, t: float, rd: float, rf: float, vol: float, phi: int = 1) -> float:
    """Garman-Kohlhagen price in quote currency per unit of base notional."""
    f, sd = forward(s, t, rd, rf), vol * math.sqrt(t)
    d1 = math.log(f / k) / sd + 0.5 * sd
    return phi * math.exp(-rd * t) * (f * N(phi * d1) - k * N(phi * (d1 - sd)))


def delta(s: float, k: float, t: float, rd: float, rf: float, vol: float, phi: int = 1, kind: str = "spot") -> float:
    """kind: spot, forward, spot_pa, forward_pa (premium-adjusted: premium paid in the base currency)."""
    f, sd = forward(s, t, rd, rf), vol * math.sqrt(t)
    d1 = math.log(f / k) / sd + 0.5 * sd
    d2 = d1 - sd
    return {"spot": phi * math.exp(-rf * t) * N(phi * d1), "forward": phi * N(phi * d1),
            "spot_pa": phi * math.exp(-rf * t) * (k / f) * N(phi * d2), "forward_pa": phi * (k / f) * N(phi * d2)}[kind]


def strike_from_delta(s: float, t: float, rd: float, rf: float, vol: float, d: float, phi: int = 1,
                      kind: str = "spot") -> float:
    """Strike with the given delta. Regular deltas in closed form; premium-adjusted ones by bisection on
    the side of the strike range where the delta is monotone (above its maximum for calls)."""
    f, sd = forward(s, t, rd, rf), vol * math.sqrt(t)
    if kind in ("spot", "forward"):
        dd = d * math.exp(rf * t) if kind == "spot" else d
        return f * math.exp(-phi * sd * n_inv(phi * dd) + 0.5 * sd * sd)
    lo, hi = f * math.exp(-8 * sd), f * math.exp(8 * sd)
    if phi == 1:                                                   # PA call delta rises then falls in K
        grid = [lo * (hi / lo) ** (i / 400) for i in range(401)]
        lo = max(grid, key=lambda k: delta(s, k, t, rd, rf, vol, 1, kind))
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        if delta(s, mid, t, rd, rf, vol, phi, kind) > d:            # deltas fall as the strike rises
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi)


def atm_dns(s: float, t: float, rd: float, rf: float, vol: float, premium_adjusted: bool = False) -> float:
    """Delta-neutral straddle strike: call delta = - put delta."""
    return forward(s, t, rd, rf) * math.exp((-0.5 if premium_adjusted else 0.5) * vol * vol * t)


def smile_vols(atm: float, rr: float, bf: float) -> tuple[float, float]:
    """(25-delta call vol, 25-delta put vol) by the simplified formula: RR = call - put, BF = the
    average of the two wings over ATM (smile strangle)."""
    return atm + bf + 0.5 * rr, atm + bf - 0.5 * rr


def quadratic_smile(points: list[tuple[float, float]]):
    """Vol as a quadratic in log-strike through three (strike, vol) points."""
    (x1, y1), (x2, y2), (x3, y3) = ((math.log(k), v) for k, v in points)

    def vol(k: float) -> float:
        x = math.log(k)
        return (y1 * (x - x2) * (x - x3) / ((x1 - x2) * (x1 - x3)) + y2 * (x - x1) * (x - x3) / ((x2 - x1) * (x2 - x3))
                + y3 * (x - x1) * (x - x2) / ((x3 - x1) * (x3 - x2)))
    return vol


def down_and_out_call(s: float, k: float, b: float, t: float, rd: float, rf: float, vol: float) -> float:
    """Down-and-out call, barrier b below spot and at or below the strike, no rebate."""
    if s <= b:
        return 0.0
    sd = vol * math.sqrt(t)
    lam = (rd - rf + 0.5 * vol * vol) / (vol * vol)
    y = math.log(b * b / (s * k)) / sd + lam * sd
    down_in = (s * math.exp(-rf * t) * (b / s) ** (2 * lam) * N(y)
               - k * math.exp(-rd * t) * (b / s) ** (2 * lam - 2) * N(y - sd))
    return gk(s, k, t, rd, rf, vol) - down_in


def barrier_delta(s: float, k: float, b: float, t: float, rd: float, rf: float, vol: float, h: float = 1e-6) -> float:
    return (down_and_out_call(s + h, k, b, t, rd, rf, vol) - down_and_out_call(s - h, k, b, t, rd, rf, vol)) / (2 * h)
