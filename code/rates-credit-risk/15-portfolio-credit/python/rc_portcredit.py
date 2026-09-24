"""Chapter 15 of Book 6: portfolio credit. An illustrative 125-name index at 50 bp (recovery 40%),
five-year tranches 0-3, 3-6, 6-9, 9-12, 12-22 and 22-100% priced in the one-factor Gaussian copula by
exact recursion; synthetic market quotes from a base-correlation skew; compound correlations (two or
none for the mezzanine); Gaussian against Student-t tails; tranche deltas; and the long-equity,
short-mezzanine trade of May 2005 hit by one name blowing out and a fall in equity correlation."""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/portcredit"))
from firm_portcredit import (  # noqa: E402
    Pool,
    base_el,
    compound_correlations,
    default_correlation,
    expected_tranche_losses,
    loss_distribution,
    simulate_losses,
    tranche_price,
)

N_NAMES, SPREAD, REC, R_FREE = 125, 0.0050, 0.40, 0.04
TRANCHES = [(0.0, 0.03), (0.03, 0.06), (0.06, 0.09), (0.09, 0.12), (0.12, 0.22), (0.22, 1.0)]
BASE_RHO = {0.03: 0.15, 0.06: 0.25, 0.09: 0.31, 0.12: 0.36, 0.22: 0.50, 1.0: 0.50}   # synthetic skew
EQ_RUNNING = 0.05


def pool(spread: float = SPREAD, blowout: float | None = None) -> Pool:
    h = np.full(N_NAMES, spread / (1 - REC))
    if blowout is not None:
        h[0] = blowout / (1 - REC)
    return Pool(h, REC)


def running(a: float) -> float:
    return EQ_RUNNING if a == 0.0 else 0.0


def market_quote(a: float, d: float, pl: Pool | None = None, rho3: float | None = None) -> dict:
    """Tranche price under the base-correlation skew (equity: upfront at 500 bp; others: par spread)."""
    pl = pl or pool()
    ra = (rho3 if (rho3 is not None and a == 0.03) else BASE_RHO.get(a, 0.0)) if a > 0 else 0.0
    rd = rho3 if (rho3 is not None and d == 0.03) else BASE_RHO[d]
    el = base_el(pl, ra, rd, a, d) if a > 0 else expected_tranche_losses(pl, rd, 0.0, d)
    return tranche_price(el, R_FREE, running(a))


def quotes() -> list[tuple[float, float, float]]:
    """(attach, detach, quote): equity upfront, others par spread."""
    out = []
    for a, d in TRANCHES:
        q = market_quote(a, d)
        out.append((a, d, q["upfront"] if a == 0 else q["par"]))
    return out


def index_spread(pl: Pool | None = None) -> float:
    return tranche_price(expected_tranche_losses(pl or pool(), 0.3, 0.0, 1.0), R_FREE, 0.0)["par"]


def compound_table():
    out = []
    for (a, d), (_, _, q) in zip(TRANCHES, quotes(), strict=True):
        out.append((a, d, compound_correlations(pool(), q, a, d, R_FREE, running(a),
                                                quote="upfront" if a == 0 else "par")))
    return out


def mezz_curve():
    """(compound rho, 3-6% par spread in bp) and the market quote."""
    return [(float(x), 1e4 * tranche_price(expected_tranche_losses(pool(), float(x), 0.03, 0.06), R_FREE, 0.0)["par"])
            for x in np.linspace(0.01, 0.95, 48)]


def loss_distribution_table(rhos=(0.05, 0.25, 0.50)):
    p = pool().pd(5.0)
    return [np.asarray(loss_distribution(p, r)) for r in rhos]


def tail_table(rho: float = 0.25, nu: float = 4.0, trials: int = 400_000):
    p = float(pool().pd(5.0)[0])
    g = simulate_losses(N_NAMES, p, rho, REC, trials, seed=11)
    t = simulate_losses(N_NAMES, p, rho, REC, trials, seed=11, nu=nu)
    xs = [0.01 * k for k in range(0, 31)]
    return [(x, float((g > x).mean()), float((t > x).mean())) for x in xs]


def seller_value(a: float, d: float, notional: float, pl: Pool, rho3: float | None = None) -> float:
    """Value to the protection seller of a tranche sold at today's market terms."""
    q0 = market_quote(a, d)
    q = market_quote(a, d, pl, rho3)
    if a == 0.0:
        return notional * (q0["upfront"] - q["upfront"])            # sold at upfront q0, 500 running
    return notional * (q0["par"] - q["par"]) * q["annuity"]            # sold at the par spread q0


def deltas(bump: float = 1e-4) -> dict:
    """Value change per 1 bp index widening (all names), per unit notional, and ratios to the index."""
    up = pool(SPREAD + bump)
    idx = (index_spread(up) - index_spread()) * tranche_price(expected_tranche_losses(pool(), 0.3, 0.0, 1.0),
                                                                R_FREE, 0.0)["annuity"]
    out = {"index": -idx}
    for a, d in TRANCHES:
        out[(a, d)] = seller_value(a, d, 1.0, up)
    out["ratio"] = {k: out[k] / out["index"] for k in TRANCHES}
    return out


def may_2005(notional: float = 10e6, blowout: float = 0.1000, rho3_after: float = 0.12) -> dict:
    """Long (sold protection on) 0-3%, hedged by buying 3-6% protection at the delta ratio."""
    dl = deltas()
    hedge = notional * dl[(0.0, 0.03)] / dl[(0.03, 0.06)]
    out = {"hedge": hedge}
    for label, pl, r3 in (("blowout", pool(blowout=blowout), None), ("corr", pool(), rho3_after),
                          ("both", pool(blowout=blowout), rho3_after)):
        eq = seller_value(0.0, 0.03, notional, pl, r3)
        mz = -seller_value(0.03, 0.06, hedge, pl, r3)
        out[label] = {"equity": eq, "mezz": mz, "total": eq + mz,
                      "eq_upfront": market_quote(0.0, 0.03, pl, r3)["upfront"],
                      "mezz_par": market_quote(0.03, 0.06, pl, r3)["par"]}
    return out


def default_corr(rho: float = 0.25) -> float:
    return default_correlation(float(pool().pd(5.0)[0]), rho)


def pd5() -> float:
    return float(pool().pd(5.0)[0])


def expected_defaults() -> float:
    return N_NAMES * pd5()


def lhp_vs_finite(rho: float = 0.25) -> tuple[float, float]:
    from firm_portcredit import lhp_expected_tranche_loss
    finite = float(expected_tranche_losses(pool(), rho, 0.0, 0.03)[-1])
    return lhp_expected_tranche_loss(0.0, 0.03, pd5(), rho, REC), finite


def super_senior_loss_prob(rho: float = 0.50) -> float:
    """P(pool loss > 22%) at five years, Gaussian copula."""
    dist = loss_distribution(pool().pd(5.0), rho)
    k = np.arange(N_NAMES + 1)
    return float(dist[(1 - REC) * k / N_NAMES > 0.22].sum())


if __name__ == "__main__":
    print(quotes(), math.nan)
