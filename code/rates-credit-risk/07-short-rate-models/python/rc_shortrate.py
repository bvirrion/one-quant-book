"""Chapter 7 of Book 6: short-rate models. Hull-White fitted to chapter 2's euro OIS curve and
calibrated to co-terminal swaptions of chapter 5's cube (a ten-year final maturity), with one sigma
and with a piecewise-constant sigma; the trinomial tree checked against Jamshidian's formula; how
mean reversion shapes the volatility of zero rates; and the correlation one factor cannot produce."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
for p in ("code/firm/shortrate", "code/rates-credit-risk/05-sabr-in-rates-and-the-volatility-cube/python"):
    sys.path.insert(0, str(ROOT / p))
import rc_sabrcube as sc  # noqa: E402
from firm_shortrate import (  # noqa: E402
    HullWhite,
    HWTree,
    calibrate_coterminal,
    g2_correlation,
    implied_normal,
    zero_rate_vol,
)

CURVE = sc.DISC
CUBE, _ = sc.build_cube()
KAPPA = 0.03
FINAL = 10
EXPIRIES = list(range(1, 10))


def atm_vol(e: int) -> float:
    n = FINAL - e
    return CUBE.normal_vol(float(e), float(n), CUBE.forward(float(e), float(n)))


def calibrations(kappa: float = KAPPA):
    return {"constant": calibrate_coterminal(CURVE, kappa, EXPIRIES, FINAL, atm_vol, constant=True),
            "piecewise": calibrate_coterminal(CURVE, kappa, EXPIRIES, FINAL, atm_vol)}


def fit_table(kappa: float = KAPPA) -> list[tuple[int, float, float, float]]:
    """(expiry, market vol bp, model vol bp with one sigma, with piecewise sigma)."""
    cal = calibrations(kappa)
    rows = []
    for e in EXPIRIES:
        n = FINAL - e
        row = [e, 1e4 * atm_vol(e)]
        for key in ("constant", "piecewise"):
            m = cal[key]
            ann, f = m.annuity_forward(e, n)
            row.append(1e4 * implied_normal(m.swaption(e, n, f), f, f, e, ann))
        rows.append(tuple(row))
    return rows


def tree_check(sigma: float = 0.0080, kappa: float = KAPPA, dt: float = 1 / 24) -> dict:
    """A 5y-into-5y at-the-money payer on the tree and by Jamshidian, constant sigma."""
    m = HullWhite(CURVE, kappa, [sigma])
    ann, f = m.annuity_forward(5, 5)
    tree = HWTree(CURVE, kappa, sigma, 10.0, dt)
    return {"jamshidian": m.swaption(5, 5, f), "tree": tree.european_swaption(5, 5, f), "forward": f,
            "annuity": ann, "bond10_tree": float(tree.zero_bonds_at(0, int(round(10 / dt)))[tree.jmax]),
            "bond10_curve": CURVE.df_t(10.0)}


def vol_term_structure() -> list[tuple[float, float, float, float]]:
    """Normal volatility (bp) of zero rates by maturity for kappa = 0, 3% and 10%, sigma = 80 bp."""
    return [(t, *[1e4 * zero_rate_vol(k, 0.0080, t) for k in (1e-9, 0.03, 0.10)]) for t in
            [0.25 * i for i in range(1, 121)]]


def g2_table(k1: float = 0.02, k2: float = 0.5, s1: float = 0.0075, s2: float = 0.0090,
             rho: float = -0.8) -> list[tuple[float, float]]:
    """Correlation of the two-year zero rate with each maturity, in G2++ (one factor: always 1)."""
    return [(t, g2_correlation(2.0, t, k1, k2, s1, s2, rho)) for t in [0.5 * i for i in range(1, 61)]]


__all__ = ["HullWhite"]
