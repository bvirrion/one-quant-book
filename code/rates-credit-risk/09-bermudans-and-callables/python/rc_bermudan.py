"""Chapter 9 of Book 6: Bermudans and callables. A ten-year euro receiver Bermudan callable annually
from year one on chapter 7's Hull-White model (kappa 3%, sigma 86 bp, chapter 2's OIS curve), by tree and
by regression Monte Carlo; its co-terminal Europeans and switch option; the effect of mean reversion;
and a thirty-year dollar callable zero-coupon bond on chapter 1's SOFR curve (the weekend problem)."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
for p in ("code/firm/bermudan", "code/firm/shortrate",
          "code/rates-credit-risk/02-multi-curve-and-collateral-discounting/python",
          "code/rates-credit-risk/01-curve-construction/python"):
    sys.path.insert(0, str(ROOT / p))
import rc_multicurve as mc  # noqa: E402
from firm_bermudan import (  # noqa: E402
    bermudan_lsm,
    bermudan_tree,
    callable_zero_tree,
    exercise_boundary,
    switch_option,
)
from firm_shortrate import HullWhite, HWTree  # noqa: E402

EUR = mc.discount()
KAPPA, SIGMA, FINAL = 0.03, 0.0086, 10
EXERCISES = list(range(1, 10))
DT = 1 / 24


def par10(curve=EUR) -> float:
    return (1.0 - curve.df_t(10.0)) / sum(curve.df_t(float(i)) for i in range(1, 11))


def bermudan_summary(kappa: float = KAPPA, sigma: float = SIGMA) -> dict:
    k = par10()
    m = HullWhite(EUR, kappa, [sigma])
    tree = HWTree(EUR, kappa, sigma, float(FINAL), DT)
    euro_tree = [bermudan_tree(tree, [e], FINAL, k) for e in EXERCISES]
    euro_exact = [m.swaption(e, FINAL - e, k, payer=False) for e in EXERCISES]
    berm = bermudan_tree(tree, EXERCISES, FINAL, k)
    return {"strike": k, "bermudan": berm, "euro_tree": euro_tree, "euro_exact": euro_exact,
            "switch": switch_option(berm, euro_tree), "best": 1 + max(range(9), key=lambda i: euro_tree[i])}


def boundary() -> list[tuple[int, float]]:
    return exercise_boundary(HWTree(EUR, KAPPA, SIGMA, float(FINAL), DT), EXERCISES, FINAL, par10())


def lsm_check(paths: int = 40000) -> tuple[float, float]:
    m = HullWhite(EUR, KAPPA, [SIGMA])
    return bermudan_lsm(m, EXERCISES, FINAL, par10(), paths)


def mean_reversion_table() -> list[tuple[float, float, float, float, float]]:
    """For kappa in (1%, 3%, 6%): sigma recalibrated so that the 5y-into-5y European equals its price at
    kappa 3% and sigma 86 bp; then (kappa, sigma bp, Bermudan bp, max European bp, switch bp)."""
    k = par10()
    target = HullWhite(EUR, KAPPA, [SIGMA]).swaption(5, 5, k, payer=False)
    rows = []
    for kap in (0.01, 0.03, 0.06):
        lo, hi = 0.002, 0.03
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if HullWhite(EUR, kap, [mid]).swaption(5, 5, k, payer=False) < target else (lo, mid)
        s = 0.5 * (lo + hi)
        r = bermudan_summary(kap, s)
        rows.append((kap, 1e4 * s, 1e4 * r["bermudan"], 1e4 * max(r["euro_tree"]), 1e4 * r["switch"]))
    return rows


# ---- the Formosa bond ---------------------------------------------------------------------------------------
def usd_curve():
    import rc_curves as rc
    return rc.curves()["monotone_convex"].curve


FORMOSA_SIGMA, FORMOSA_KAPPA = 0.0090, 0.03


def formosa(accretion: float, sigma: float = FORMOSA_SIGMA, maturity: int = 30, first_call: int = 5,
            dt: float = 1 / 12) -> dict:
    tree = HWTree(usd_curve(), FORMOSA_KAPPA, sigma, float(maturity), dt)
    calls = list(range(first_call, maturity))
    full = callable_zero_tree(tree, maturity, accretion, calls)
    euros = [callable_zero_tree(tree, maturity, accretion, [c])["option"] for c in calls]
    return {**full, "best_euro": max(euros), "best_call": calls[max(range(len(euros)), key=lambda i: euros[i])]}


def formosa_par_yield(sigma: float = FORMOSA_SIGMA) -> float:
    """Accretion yield at which the callable zero is worth par (1) today."""
    lo, hi = 0.045, 0.065
    for _ in range(22):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if formosa(mid, sigma)["callable"] < 1.0 else (lo, mid)
    return 0.5 * (lo + hi)
