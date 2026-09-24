"""Greek calculator in desk units (build of Book 5, Chapter 4).

Any pricer is a function of keyword parameters (spot, vol, r, t, ...). Greeks are computed by
central bump-and-reprice with the desk's standard shifts, or converted from analytic Greeks
(firm_bs.greeks), and reported in money units:
  delta      per unit of spot (shares);        cash_delta = delta * S (currency)
  gamma      per unit of spot squared;         gamma_1pct = Gamma S^2 / 100: change of cash delta for +1 %
  cash_gamma = 1/2 Gamma S^2: P&L per unit of squared return (1/2 Gamma dS^2 = cash_gamma (dS/S)^2)
  vega_pt    per volatility point (0.01);      theta_day per calendar day;   rho_bp per basis point
"""
from collections.abc import Callable

DAY = 1.0 / 365.0


def bump_greeks(pricer: Callable[..., float], params: dict, h_spot: float = 0.01, h_vol: float = 0.01,
                h_rate: float = 1e-4, days: float = 1.0) -> dict[str, float]:
    """Central differences for delta, gamma, vega, rho; a forward roll of `days` for theta."""
    s, v0 = params["spot"], pricer(**params)

    def at(**kw) -> float:
        return pricer(**{**params, **kw})
    up, dn = at(spot=s * (1 + h_spot)), at(spot=s * (1 - h_spot))
    delta = (up - dn) / (2 * h_spot * s)
    gamma = (up - 2 * v0 + dn) / (h_spot * s) ** 2
    vega_pt = (at(vol=params["vol"] + h_vol) - at(vol=params["vol"] - h_vol)) / 2 * (0.01 / h_vol)
    rho_bp = (at(r=params["r"] + h_rate) - at(r=params["r"] - h_rate)) / 2 * (1e-4 / h_rate)
    theta_day = (at(t=max(params["t"] - days * DAY, 0.0)) - v0) / days
    return desk_units({"value": v0, "delta": delta, "gamma": gamma}, s) | {"vega_pt": vega_pt, "rho_bp": rho_bp,
                                                                          "theta_day": theta_day}


def desk_units(g: dict[str, float], spot: float) -> dict[str, float]:
    """Add cash delta, gamma per 1 % and cash gamma to raw delta/gamma; convert analytic vega (per unit
    vol), theta (per year) and rho (per unit rate) when present."""
    out = dict(g)
    out["cash_delta"] = g["delta"] * spot
    out["gamma_1pct"] = g["gamma"] * spot * spot / 100.0
    out["cash_gamma"] = 0.5 * g["gamma"] * spot * spot
    if "vega" in g:
        out["vega_pt"] = g["vega"] * 0.01
    if "theta" in g:
        out["theta_day"] = g["theta"] * DAY
    if "rho" in g:
        out["rho_bp"] = g["rho"] * 1e-4
    return out


def predict_pnl(g: dict[str, float], d_spot: float, d_vol_pts: float = 0.0, days: float = 1.0) -> float:
    """Taylor prediction of the next P&L: delta dS + 1/2 Gamma dS^2 + vega dvol + theta dt."""
    return (g["delta"] * d_spot + 0.5 * g["gamma"] * d_spot * d_spot + g["vega_pt"] * d_vol_pts
            + g["theta_day"] * days)


def hedging_pnl(cash_gamma: float, ret: float, vol_hedge: float, dt: float) -> float:
    """Gamma-theta identity for a long, delta-hedged option over one step (r = 0):
    cash_gamma * (ret^2 - vol_hedge^2 dt)."""
    return cash_gamma * (ret * ret - vol_hedge * vol_hedge * dt)


def breakeven_vol(theta_day: float, cash_gamma: float, days_per_year: float = 365.0) -> float:
    """Annualised volatility at which a day's gamma P&L pays the day's theta."""
    return (-theta_day / cash_gamma * days_per_year) ** 0.5
