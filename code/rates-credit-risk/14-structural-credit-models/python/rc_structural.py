"""Chapter 14 of Book 6: structural credit. An illustrative leveraged firm (equity 10, debt face 40
due in five years, equity volatility 50%, in USD billions): Merton inversion, distance to default,
Merton term structures of spreads, a Black-Cox first-passage model with a barrier at a fraction L of
the debt face, the model's equity-to-spread hedge ratio, and a capital-structure trade (sell protection,
short equity) caught by an equity rally and a spread widening on consecutive days."""
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
for p in ("code/firm/structural", "code/firm/cdscurve"):
    sys.path.insert(0, str(ROOT / p))
from firm_cdscurve import standard_upfront  # noqa: E402
from firm_structural import (  # noqa: E402
    asset_from_equity,
    distance_to_default,
    first_passage_survival,
    invert,
    merton_debt,
    merton_equity,
    merton_pd,
    merton_spread,
    model_cds_spread,
)

E0, SIGMA_E, D, T, R_FREE, MU, REC = 10.0, 0.50, 40.0, 5.0, 0.04, 0.08, 0.40
L_BARRIER = 0.70                 # barrier as a fraction of the debt face (set from the firm's history)
MARKET_SPREAD, COUPON, NOTIONAL = 0.0500, 0.0500, 10e6


def firm() -> dict:
    V, s = invert(E0, SIGMA_E, D, T, R_FREE)
    return {"V": V, "sigma": s, "debt": merton_debt(V, D, T, R_FREE, s),
            "leverage": D * math.exp(-R_FREE * T) / V,
            "spread": merton_spread(V, D, T, R_FREE, s),
            "pd_rn": merton_pd(V, D, T, R_FREE, s), "pd_real": merton_pd(V, D, T, MU, s),
            "dd": distance_to_default(V, D, T, MU, s)}


def fp_spread(V: float, sigma: float, maturity: float = T, L: float = L_BARRIER) -> float:
    return model_cds_spread(lambda t: first_passage_survival(V, L * D, t, R_FREE, sigma), R_FREE, maturity, REC)


def fp_survival(V: float, sigma: float, t: float, L: float = L_BARRIER) -> float:
    return first_passage_survival(V, L * D, t, R_FREE, sigma)


def implied_barrier(spread: float = MARKET_SPREAD) -> float:
    f = firm()
    lo, hi = 0.3, 0.99
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if fp_spread(f["V"], f["sigma"], T, mid) < spread else (lo, mid)
    return 0.5 * (lo + hi)


def model_spread_at_equity(E: float) -> float:
    """First-passage five-year spread when equity moves to E with the asset volatility held."""
    f = firm()
    return fp_spread(asset_from_equity(E, f["sigma"], D, T, R_FREE), f["sigma"])


def seller_value(spread: float, notional: float = NOTIONAL) -> float:
    """Mark of sold five-year protection at the 500 bp coupon when the market quotes `spread`."""
    return -notional * standard_upfront(T, spread, COUPON, R_FREE, REC)


def hedge() -> dict:
    """Equity short (USD) that offsets the sold protection for small equity moves, by the model."""
    h = 1e-3
    ds_dE = (model_spread_at_equity(E0 + h) - model_spread_at_equity(E0 - h)) / (2 * h)
    dv_ds = (seller_value(MARKET_SPREAD + 1e-5) - seller_value(MARKET_SPREAD - 1e-5)) / 2e-5
    dv_dE = dv_ds * ds_dE                          # USD per USD billion of equity value
    return {"ds_dE": ds_dE, "cs01": dv_ds * 1e-4, "dv_dE": dv_dE, "short_equity": dv_dE * E0}


def may_2005(equity_move: float = 0.18, market_widening: float = 0.0200) -> dict:
    """Consecutive days: equity up `equity_move` (model spread tightens), then the market spread widens."""
    hd = hedge()
    s_model0, s_model1 = model_spread_at_equity(E0), model_spread_at_equity(E0 * (1 + equity_move))
    predicted = MARKET_SPREAD + (s_model1 - s_model0)
    eq_pnl = -hd["short_equity"] * equity_move
    out = {"model0": s_model0, "model1": s_model1, "predicted": predicted, "equity_pnl": eq_pnl,
           "cds_pnl_model": seller_value(predicted) - seller_value(MARKET_SPREAD),
           "cds_pnl": seller_value(MARKET_SPREAD + market_widening) - seller_value(MARKET_SPREAD)}
    out["hedged_model"] = out["cds_pnl_model"] + eq_pnl
    out["total"] = out["cds_pnl"] + eq_pnl
    return out


def equity_debt_table():
    """(asset value, equity today, debt today, equity payoff at maturity) for the calibrated volatility."""
    s = firm()["sigma"]
    return [(v, merton_equity(v, D, T, R_FREE, s), merton_debt(v, D, T, R_FREE, s), max(v - D, 0.0))
            for v in [2.0 * k for k in range(1, 41)]]


def merton_term_structure(quasi_leverage: float, sigma: float = 0.25):
    """Merton yield spreads (bp) against maturity at a fixed quasi-leverage D e^{-rT} / V (Merton 1974)."""
    out = []
    for k in range(1, 81):
        t = k / 8
        out.append((t, max(1e4 * merton_spread(1.0, quasi_leverage * math.exp(R_FREE * t), t, R_FREE, sigma), 0.0)))
    return out


def fp_term_structure(L: float):
    f = firm()
    return [(t, 1e4 * fp_spread(f["V"], f["sigma"], t, L)) for t in (0.5, 1, 1.5, 2, 3, 4, 5, 6, 7, 8, 9, 10)]


def equity_spread_curve():
    return [(e, 1e4 * model_spread_at_equity(e)) for e in [6.0 + 0.25 * k for k in range(41)]]
