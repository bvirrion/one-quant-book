"""firm.rfqmm -- automated request-for-quote market making in bonds and ETFs (One Quant Book 11, chapter 22).

Built on Book 2's firm.rfq (the RFQ auction's order statistics and the composite price). Prices in cents per 100
of face value.

A client sells a bond by request for quote to n dealers (we are one). Each dealer estimates the bond's value with its
own error (standard deviation `sigma_est`, the bond has not traded for weeks) and bids its estimate less a markup; the
client sells to the best bid if it is at least its reservation price (value less an exponential urgency discount). The
winner of a sale is the dealer that overestimated most: the winner's curse.

API (stable):
    fair_value(prints, ages_days, comps, comp_betas, curve_move, half_life)
                                                     a bond's value from its own stale prints (composite, firm.rfq)
                                                     moved by its issuer curve since, blended with comparables
    simulate(n_dealers, our_markup, n, seed, sigma_est, comp_markup, urgency)
                                                     per request: whether we won, our P&L if so, the cover (second-best
                                                     bid) and the client's choice
    optimise(n_dealers, markups, ...)                expected P&L per request and win rate by markup; the best markup
    equilibrium(n_dealers, markups, ...)             the symmetric equilibrium markup and its P&L, win rate, curse
    naive_markup(history, markups)                   the markup a model ignoring the winner's curse would choose
    fit_win_model(markups, wins)                     logistic P(win | markup) by Newton's method
    etf_rfq_bid(basket_bid, units, creation_fee, redemption_cost_bp, hedge_bp)
                                                     a bid for an ETF block priced from its creation basket
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "rfq"))
import firm_rfq as rfq  # noqa: E402


def fair_value(prints, ages_days, comps, comp_betas, curve_move: float, half_life: float = 5.0,
               w_comps: float = 0.5) -> float:
    """The composite of the bond's own prints (recency-weighted, outliers dropped; ages in days as firm.rfq's
    seconds) moved by its issuer curve's move since, blended with the mean of comparables' prices times their betas."""
    own = rfq.composite(list(zip(prints, ages_days, strict=True)), half_life=half_life) + curve_move
    comp = float(np.mean(np.asarray(comps, float) * np.asarray(comp_betas, float)))
    return (1.0 - w_comps) * own + w_comps * comp


def simulate(n_dealers: int, our_markup: float, n: int = 40000, seed: int = 0, sigma_est: float = 25.0,
             comp_markup: float = 15.0, urgency: float = 30.0, our_sigma: float | None = None) -> dict:
    """All in cents per 100 face; `our_sigma` (default sigma_est) is our own estimate's error. Returns arrays over
    requests: win, pnl (value - our bid, if we win), cover (best competing bid relative to value), our error,
    traded (the client sold to someone)."""
    rng = np.random.default_rng(seed)
    e = rng.standard_normal((n, n_dealers)) * sigma_est
    if our_sigma is not None:
        e[:, 0] *= our_sigma / sigma_est
    bids = e.copy()
    bids[:, 0] -= our_markup
    bids[:, 1:] -= comp_markup
    reservation = -rng.exponential(urgency, n)
    best = bids.max(axis=1)
    traded = best >= reservation
    win = traded & (bids[:, 0] >= best)
    pnl = np.where(win, -bids[:, 0], 0.0)
    cover = bids[:, 1:].max(axis=1) if n_dealers > 1 else np.full(n, -np.inf)
    return {"win": win, "pnl": pnl, "cover": cover, "our_error": e[:, 0], "traded": traded, "our_bid": bids[:, 0]}


def optimise(n_dealers: int, markups, **kw) -> dict:
    rows = {}
    for m in markups:
        s = simulate(n_dealers, float(m), **kw)
        w = s["win"]
        rows[float(m)] = {"pnl": float(s["pnl"].mean()), "win": float(w.mean()),
                          "pnl_per_win": float(s["pnl"][w].mean()) if w.any() else 0.0,
                          "curse": float(s["our_error"][w].mean()) if w.any() else 0.0}
    best = max(rows, key=lambda k: rows[k]["pnl"])
    return {"rows": rows, "best": best}


def equilibrium(n_dealers: int, markups, iters: int = 12, **kw) -> dict:
    """Symmetric equilibrium: the markup that is our best response when every competitor uses it (damped
    best-response iteration on the markup grid)."""
    m = float(markups[len(markups) // 2])
    for _ in range(iters):
        o = optimise(n_dealers, markups, comp_markup=m, **kw)
        new = o["best"]
        if new == m:
            break
        m = new
    o = optimise(n_dealers, markups, comp_markup=m, **kw)
    return {"markup": m, **o["rows"][m], "rows": o["rows"]}


def naive_markup(rows: dict) -> float:
    """Maximise win probability x markup, as if the bid's error were zero once the request is won."""
    return max(rows, key=lambda m: rows[m]["win"] * m)


def fit_win_model(markups, wins, iters: int = 50) -> tuple[float, float]:
    """Logistic P(win) = 1 / (1 + exp(-(a + b m))) fitted by Newton's method."""
    x = np.asarray(markups, float)
    y = np.asarray(wins, float)
    X = np.column_stack([np.ones_like(x), x])
    beta = np.zeros(2)
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-(X @ beta)))
        W = p * (1 - p)
        H = X.T @ (X * W[:, None]) + 1e-9 * np.eye(2)
        beta += np.linalg.solve(H, X.T @ (y - p))
    return float(beta[0]), float(beta[1])


def etf_rfq_bid(basket_bid: float, units: int, creation_fee: float, redemption_cost_bp: float,
                hedge_bp: float) -> float:
    """Per share: the basket's bid less the redemption's costs (the fee spread over the unit's shares and the basket's
    selling cost) less the cost of hedging while the redemption settles."""
    return basket_bid * (1.0 - (redemption_cost_bp + hedge_bp) * 1e-4) - creation_fee / units
