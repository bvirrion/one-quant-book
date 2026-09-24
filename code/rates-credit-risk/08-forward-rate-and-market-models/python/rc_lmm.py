"""Chapter 8 of Book 6: forward-rate and market models. A ten-forward annual market model on chapter 2's
euro OIS curve, calibrated to caplets (normal volatility 70 bp at every expiry, converted to Black),
simulated under the spot measure; caplets and swaptions by Monte Carlo against Black and Rebonato;
two correlation parametrisations that fit the same caplets and disagree on swaptions."""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for p in ("code/firm/lmm", "code/rates-credit-risk/02-multi-curve-and-collateral-discounting/python"):
    sys.path.insert(0, str(ROOT / p))
import rc_multicurve as mc  # noqa: E402
from firm_lmm import (  # noqa: E402
    LMM,
    abcd,
    black,
    calibrate_to_caplets,
    hjm_drift_gaussian,
    implied_black,
    mc_caplet,
    mc_swaption,
    rebonato_vol,
)

N = 10
DISC = mc.discount()
F0 = np.array([(DISC.df_t(k) / DISC.df_t(k + 1) - 1.0) if k > 0 else (1 / DISC.df_t(1.0) - 1.0) for k in range(N)])
NORMAL_VOL = 0.0070
CAPLET_BLACK = NORMAL_VOL / F0
ABCD = (0.05, 0.10, 0.60, 0.15)


def model(beta: float = 0.10) -> LMM:
    return calibrate_to_caplets(F0, CAPLET_BLACK, ABCD, beta)


def caplet_check(paths: int = 20000) -> list[tuple[int, float, float, float]]:
    """(expiry k, target Black vol %, MC implied Black vol %, 2 standard errors in vol %) at the money."""
    m = model()
    p = m.discount_factors()
    rows = []
    for k in (1, 2, 3, 5, 7, 9):
        price, se = mc_caplet(m, k, m.f0[k], paths, seed=11 + k)
        ann = m.delta * p[k + 1]
        v = implied_black(price, m.f0[k], m.f0[k], k, ann)
        v_hi = implied_black(price + 2 * se, m.f0[k], m.f0[k], k, ann)
        rows.append((k, 100 * CAPLET_BLACK[k], 100 * v, 100 * (v_hi - v)))
    return rows


def swaption_table(betas=(0.02, 0.40), a: int = 5, paths: int = 20000) -> list[tuple]:
    """For swaptions a into 1..5 years: (tenor, [Rebonato vol %, MC vol %] per beta)."""
    rows = []
    for tenor in range(1, 6):
        row = [tenor]
        for beta in betas:
            m = model(beta)
            s, ann, _ = m.swap(a, a + tenor)
            price, _ = mc_swaption(m, a, a + tenor, s, paths, seed=101 + tenor)
            row += [100 * rebonato_vol(m, a, a + tenor), 100 * implied_black(price, s, s, a, ann)]
        rows.append(tuple(row))
    return rows


def correlation_rows(betas=(0.02, 0.10, 0.40)) -> list[tuple]:
    return [(j, *[math.exp(-b * abs(j - 1)) for b in betas]) for j in range(1, N)]


def abcd_curve() -> list[tuple[float, float]]:
    return [(t, float(abcd(t, *ABCD))) for t in np.linspace(0, 10, 101)]


def hw_as_hjm(sigma: float = 0.008, kappa: float = 0.03) -> list[tuple[float, float]]:
    """HJM drift (bp per year) of the forward at maturity T, seen at 0, for Hull-White volatilities."""
    return [(float(T), 1e4 * hjm_drift_gaussian(0.0, float(T), sigma, kappa)) for T in np.linspace(0, 30, 61)]


__all__ = ["LMM", "black"]
