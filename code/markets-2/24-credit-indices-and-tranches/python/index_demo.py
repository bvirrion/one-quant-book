"""Chapter 24 of Book 2: credit indices and tranches. A stylised 125-name investment-grade index
(spreads spread log-normally around a median), its intrinsic spread and skew, the P&L of a skew
trade, and tranche expected losses in the one-factor Gaussian large-pool model. All parameters are
illustrative; pricing uses the chapter 23 CDS build (five years, 4% flat rate, 40% recovery)."""
import math
import pathlib
import sys
from statistics import NormalDist

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/cds"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/tranche"))
from firm_cds import Cds, hazard_from_spread, legs, upfront_from_spread
from firm_tranche import (
    annuity_weighted_spread,
    base_correlation,
    expected_tranche_loss,
    intrinsic_upfront,
    simulate_pool,
    skew_pnl,
)

R_FREE, RECOVERY, NAMES = 0.04, 0.40, 125
INDEX = Cds(5.0, 0.01)                         # the index trades like a five-year CDS with a 100 bp coupon
MEDIAN, DISPERSION = 0.0055, 0.8
SPREADS = [MEDIAN * math.exp(DISPERSION * NormalDist().inv_cdf((i - 0.5) / NAMES)) for i in range(1, NAMES + 1)]
TRANCHES = [(0.0, 0.03), (0.03, 0.07), (0.07, 0.15), (0.15, 1.0)]
NOTIONAL, SKEW_BP = 1e9, -8.0                   # the skew trade: index quoted 8 bp through intrinsic
HALF_SPREAD_SINGLE, HALF_SPREAD_INDEX = 1.5, 0.25   # bp of running spread paid to trade


def upfront(spread: float) -> float:
    return upfront_from_spread(INDEX, spread, R_FREE)


def spread_from_upfront(u: float) -> float:
    lo, hi = 1e-6, 0.5
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if upfront(mid) < u else (lo, mid)
    return 0.5 * (lo + hi)


def annuity(spread: float) -> float:
    return legs(INDEX, hazard_from_spread(INDEX, spread, R_FREE), R_FREE)[0]


def intrinsic() -> dict[str, float]:
    ups = [upfront(s) for s in SPREADS]
    iu = intrinsic_upfront(ups)
    s_int = spread_from_upfront(iu)
    return {"average": sum(SPREADS) / NAMES, "median": MEDIAN, "min": min(SPREADS), "max": max(SPREADS),
            "upfront": iu, "intrinsic": s_int, "annuity": annuity(s_int),
            "weighted": annuity_weighted_spread(SPREADS, [annuity(s) for s in SPREADS])}


def default_probability(spread: float, years: float = 5.0) -> float:
    return 1.0 - math.exp(-hazard_from_spread(INDEX, spread, R_FREE) * years)


def skew_trade() -> dict[str, float]:
    it = intrinsic()
    entry = it["intrinsic"] + SKEW_BP / 1e4
    u0 = upfront(entry)
    pnl = {k: skew_pnl(NOTIONAL, u0, upfront(it["intrinsic"] + x / 1e4)) for k, x in (("close", 0.0), ("widen", -20.0))}
    single_cost = NOTIONAL * HALF_SPREAD_SINGLE / 1e4 * it["annuity"]
    index_cost = NOTIONAL * HALF_SPREAD_INDEX / 1e4 * it["annuity"]
    per_name = NOTIONAL / NAMES
    return {"entry": entry, "u_index": u0, "u_intrinsic": it["upfront"], "pnl_close": pnl["close"],
            "pnl_widen": pnl["widen"], "single_cost": single_cost, "index_cost": index_cost,
            "round_trip_cost": 2 * (single_cost + index_cost), "per_name": per_name,
            "default_payout": per_name * (1 - RECOVERY), "net_close": pnl["close"] - 2 * (single_cost + index_cost),
            "breakeven_bp": 2 * (HALF_SPREAD_SINGLE + HALF_SPREAD_INDEX)}


def skew_pnl_curve(lo: int = -24, hi: int = 8) -> list[tuple[int, float]]:
    it = intrinsic()
    u0 = upfront(it["intrinsic"] + SKEW_BP / 1e4)
    return [(x, skew_pnl(NOTIONAL, u0, upfront(it["intrinsic"] + x / 1e4)) / 1e6) for x in range(lo, hi + 1)]


def tranche_table(rhos: tuple[float, ...] = tuple(k / 20 for k in range(1, 19))) -> list[tuple[float, ...]]:
    p = default_probability(intrinsic()["intrinsic"])
    return [(rho, *(expected_tranche_loss(a, d, p, rho, RECOVERY) for a, d in TRANCHES)) for rho in rhos]


def loss_histograms(rhos: tuple[float, ...] = (0.1, 0.4), k_max: int = 40):
    """Probability of k defaults among the 125 names (k_max collects k >= k_max), and the pool loss."""
    p = default_probability(intrinsic()["intrinsic"])
    out = []
    for rho in rhos:
        sims = simulate_pool(NAMES, p, rho, RECOVERY, trials=20_000, seed=int(100 * rho))
        counts = [0] * (k_max + 1)
        for x in sims:
            counts[min(round(x / (1 - RECOVERY) * NAMES), k_max)] += 1
        out.append((rho, [(k, 100 * k * (1 - RECOVERY) / NAMES, c / len(sims)) for k, c in enumerate(counts)]))
    return out


def tutorial() -> dict[str, float]:
    it = intrinsic()
    p = default_probability(it["intrinsic"])
    mezz = [expected_tranche_loss(0.03, 0.07, p, rho, RECOVERY) for rho in (0.1, 0.2, 0.45)]
    eq = expected_tranche_loss(0.0, 0.03, p, 0.25, RECOVERY)
    return {**it, "p": p, "eq_25": eq, "base_corr": base_correlation(0.03, eq, p, RECOVERY),
            "mezz_10": mezz[0], "mezz_20": mezz[1], "mezz_45": mezz[2],
            "pool_el": p * (1 - RECOVERY)}
