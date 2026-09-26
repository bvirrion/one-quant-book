"""One Quant Book 10, chapter 22: pricing a risk bid on a 500-name basket, disclosed and blind.

    universe()                 names of firm.synthmkt's synthetic market listed on its last day: price, daily dollar
                               volume, daily volatility, sector, beta; half-spreads from a size rule (an assumption);
                               a statistical risk model (firm.riskmodel.pca_model, 10 factors) on the last 250 days
    basket(seed)               a pension fund's 500-name basket, USD 250 million, weights rising with dollar volume
    price(names, notional)     liquidation cost (20% participation cap), the risk carried with and without a market
                               hedge, in basis points of the basket
    blind(seed)                what a dealer who sees only the liquidity profile can know: the cost and risk of 300
                               baskets with the same notional in every sector x days-of-volume cell
    bids()                     the disclosed and blind bids: cost + risk charge + winner's-curse shading against three
                               competitors + margin, and the auction check of the shading
    transition_study()         a transition between two 300-name portfolios: selling and buying everything, netting
                               the shared names, and crossing 20% of the rest internally
All deterministic (fixed seeds).
"""
from __future__ import annotations

import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("riskbid", "synthmkt", "riskmodel", "rfq"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_riskbid import auction, curse, liquidation, profile, risk_sd, transition  # noqa: E402
from firm_riskmodel import pca_model  # noqa: E402
from firm_synthmkt import MarketConfig, simulate  # noqa: E402

GROSS, NAMES = 250e6, 500
CAP, Y = 0.2, 0.7
RISK_K, MARGIN, EST_ERR, COMPETITORS = 1.0, 2.0, 0.15, 3
EDGES = (0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 1.0)


@functools.cache
def universe(seed: int = 22) -> dict:
    p = simulate(MarketConfig(n=800, days=260, seed=seed))
    r = p.ret[-250:]
    ok = p.listed[-1] & np.all(np.isfinite(r), axis=0)
    idx = np.nonzero(ok)[0]
    r = r[:, idx]
    price = p.price[-1, idx]
    adv = np.nanmean(p.volume[-60:, idx] * p.price[-60:, idx], axis=0)
    sigma = r.std(axis=0, ddof=1) * 1e4
    spread = np.clip(1.0 + 3e4 / np.sqrt(adv), 1.0, 60.0)             # bp: a size rule (assumption)
    b, f, s = pca_model(r, 10)
    cov = b @ f @ b.T + np.diag(s)
    return {"idx": idx, "price": price, "adv": adv, "sigma": sigma, "spread": spread, "sector": p.industry[idx],
            "beta": p.beta[idx], "mkt_var": float(np.var(p.mkt[-250:], ddof=1)), "cov": cov}


def basket(seed: int = 7) -> tuple[np.ndarray, np.ndarray]:
    u = universe()
    rng = np.random.default_rng(seed)
    names = np.sort(rng.choice(len(u["adv"]), NAMES, replace=False))
    w = np.sqrt(u["adv"][names]) * rng.lognormal(0.0, 0.5, NAMES)
    return names, GROSS * w / w.sum()


def price(names, notional) -> dict:
    u = universe()
    liq = liquidation(notional, u["adv"][names], u["sigma"][names], u["spread"][names], CAP, Y)
    cov = u["cov"][np.ix_(names, names)]
    raw = risk_sd(notional, cov, liq["days"])
    hedged = risk_sd(notional, cov, liq["days"], hedge=(u["beta"][names], u["mkt_var"]))
    g = float(np.sum(notional))
    return {"cost": liq["total_bp"], "risk": raw / g * 1e4, "risk_hedged": hedged / g * 1e4,
            "days_max": float(liq["days"].max()), "over_one_day": float(np.sum(notional[liq["days"] > 1]) / g)}


@functools.cache
def blind(seed: int = 7, draws: int = 300) -> dict:
    """Baskets with the disclosed one's profile: each position keeps its sector, its notional and its bucket of days
    of volume, but its name is drawn from the universe's names that satisfy them."""
    u = universe()
    names, notional = basket(seed)
    edges = np.asarray(EDGES)
    cell = np.searchsorted(edges, notional / u["adv"][names])
    rng = np.random.default_rng(seed + 100)
    cand = [np.nonzero((u["sector"] == u["sector"][i]) & (np.searchsorted(edges, q / u["adv"]) == c))[0]
            for i, q, c in zip(names, notional, cell, strict=True)]
    costs, risks = [], []
    for _ in range(draws):
        pick = np.array([rng.choice(c) for c in cand])
        pick, first = np.unique(pick, return_index=True)          # a name drawn twice keeps its first position
        pr = price(pick, notional[first] * notional.sum() / notional[first].sum())
        costs.append(pr["cost"])
        risks.append(pr["risk_hedged"])
    return {"cost": (float(np.mean(costs)), float(np.std(costs, ddof=1))),
            "risk": (float(np.mean(risks)), float(np.std(risks, ddof=1))),
            "profile": profile(notional, u["adv"][names], u["sector"][names], EDGES)}


@functools.cache
def bids(seed: int = 7) -> dict:
    names, notional = basket(seed)
    d = price(names, notional)
    b = blind(seed)
    out = {"disclosed_true": d}
    base_d = d["cost"] + RISK_K * d["risk_hedged"]
    sig_d = EST_ERR * base_d
    base_b = b["cost"][0] + RISK_K * b["risk"][0]
    sig_b = math.sqrt(sig_d**2 + b["cost"][1] ** 2 + (RISK_K * b["risk"][1]) ** 2)
    for name, base, sig in (("disclosed", base_d, sig_d), ("blind", base_b, sig_b)):
        shade = curse(sig, COMPETITORS)
        out[name] = {"base": base, "sigma_est": sig, "curse": shade, "bid": base + shade + MARGIN,
                     "naive_profit": auction(base_d, sig, COMPETITORS + 1, 0.0, MARGIN, 200_000, 3),
                     "shaded_profit": auction(base_d, sig, COMPETITORS + 1, shade, MARGIN, 200_000, 3)}
    return out


@functools.cache
def transition_study(seed: int = 11, cross_share: float = 0.2) -> dict:
    u = universe()
    rng = np.random.default_rng(seed)
    n = len(u["adv"])
    old_names = rng.choice(n, 300, replace=False)
    keep = old_names[:150]
    new_names = np.concatenate([keep, rng.choice(np.setdiff1d(np.arange(n), old_names), 150, replace=False)])
    w_old = rng.lognormal(0, 0.5, 300)
    w_new = rng.lognormal(0, 0.5, 300)
    old = dict(zip(old_names.tolist(), (GROSS * w_old / w_old.sum()).tolist(), strict=True))
    new = dict(zip(new_names.tolist(), (GROSS * w_new / w_new.sum()).tolist(), strict=True))
    t = transition(old, new, cross_share)

    def cost(trades: dict, scale: float = 1.0) -> float:
        k = np.array(sorted(trades))
        q = np.array([trades[i] for i in k]) * scale
        return liquidation(q, u["adv"][k], u["sigma"][k], u["spread"][k], CAP, Y)["total_bp"] * q.sum()
    full = cost(old) + cost(new)
    diff = {k: new.get(k, 0.0) - old.get(k, 0.0) for k in set(old) | set(new)}
    netted = cost({k: abs(v) for k, v in diff.items() if abs(v) > 0})
    crossed_scale = t["crossed"] / t["netted"]
    crossed = cost({k: abs(v) for k, v in diff.items() if abs(v) > 0}, crossed_scale)
    return t | {"cost_full": full / GROSS, "cost_netted": netted / GROSS, "cost_crossed": crossed / GROSS}
