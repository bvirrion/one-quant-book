"""firm.mbsrv -- prepayment-view trades, IO/PO valuation and tranche relative value (build of Book 9, chapter 20).

The market prices agency pass-throughs, and the interest-only (IO) and principal-only (PO) strips cut from them,
with one prepayment model (Book 6's `firm_mbsoas`: turnover, a refinancing S-curve and burnout) at one option-
adjusted spread, on Hull-White paths around a flat curve. A trader holds a different view of the borrowers. Each
strip is valued under the model that turns out to be true, at the market's OAS and after a parallel shift of the
curve; the trade's gain is that value less the market price, plus a ten-year Treasury hedge sized to remove the rate
risk the market model sees. The same machinery gives each coupon's OAS under the two models (the coupon stack).
Tranches use Book 2's large-pool Gaussian copula (`firm_tranche`): expected tranche loss at the market's correlation
against the loss realised when names default with another correlation. NumPy only.

API (stable):
    MbsConfig(...)                              parameters (seed 163)
    FlatCurve(rate)                             a flat zero curve with df_t(t)
    strip_paths(cfg, model, wac, oas, shift)    per-path PVs (paths,) of the IO, PO and pass-through
    io_trade(cfg, market, truth, side, shifts)  hedged gain of buying (+1) or selling (-1) the IO at the market price,
                                                by parallel shift of the curve
    coupon_stack(cfg, market, view, wacs)       per coupon: market price, the view's OAS, durations
    tranche_rv(p, rho_market, rho_true, ...)    expected tranche loss at both correlations; selling protection
                                                at the market's price, realised on simulated pools
"""
from __future__ import annotations

import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

HERE = pathlib.Path(__file__).resolve().parents[1]
for comp in ("mbsoas", "tranche"):
    sys.path.insert(0, str(HERE / comp))
from firm_mbsoas import Pool, PrepayModel, pool_flows, pv_paths, simulate_paths, solve_oas  # noqa: E402
from firm_tranche import expected_tranche_loss, simulate_pool, tranche_loss  # noqa: E402


@dataclass(frozen=True)
class MbsConfig:
    rate: float = 0.04            # flat zero rate
    kappa: float = 0.03           # Hull-White mean reversion
    sigma: float = 0.009          # Hull-White short-rate vol
    paths: int = 2000
    seed: int = 163
    wac: float = 0.065            # borrowers' rate of the traded pool; the coupon is 50 bp lower
    term: int = 360
    age: int = 12
    market_oas: float = 0.005
    hedge_years: int = 10         # the Treasury hedge: a bullet at the par rate


class FlatCurve:
    def __init__(self, rate: float):
        self.rate = rate

    def df_t(self, t: float) -> float:
        return math.exp(-self.rate * t)


def _paths(cfg: MbsConfig, shift: float = 0.0):
    return simulate_paths(FlatCurve(cfg.rate), cfg.kappa, cfg.sigma, cfg.term - cfg.age, cfg.paths, cfg.seed, shift)


def strip_paths(cfg: MbsConfig, model: PrepayModel, wac: float | None = None, oas: float | None = None,
                shift: float = 0.0) -> dict:
    wac = cfg.wac if wac is None else wac
    oas = cfg.market_oas if oas is None else oas
    rs, p10 = _paths(cfg, shift)
    io, po = pool_flows(Pool(wac=wac, coupon=wac - 0.005, term=cfg.term, age=cfg.age), model, p10)
    return {"io": pv_paths(io, rs, oas), "po": pv_paths(po, rs, oas), "pt": pv_paths(io + po, rs, oas), "rs": rs,
            "flows": io + po}


def _treasury(cfg: MbsConfig, shift: float = 0.0) -> np.ndarray:
    rs, _ = _paths(cfg, shift)
    n = 12 * cfg.hedge_years
    flows = np.zeros(rs.shape[1])
    flows[5:n:6] = 100 * cfg.rate / 2
    flows[n - 1] += 100
    return pv_paths(np.broadcast_to(flows, rs.shape), rs, 0.0)


def io_trade(cfg: MbsConfig, market: PrepayModel, truth: PrepayModel, side: float = 1.0, shifts=(0.0,),
             dy: float = 0.0025) -> dict:
    """Buy (side +1) or sell (-1) the IO at the market model's value, and hedge the rate risk the market model measures
    with the ten-year Treasury. For each parallel shift of the curve: the IO's value under the true model less the
    price paid, plus the hedge's change; in % of the price."""
    price = strip_paths(cfg, market)["io"].mean()
    dv_io = strip_paths(cfg, market, shift=-dy)["io"].mean() - strip_paths(cfg, market, shift=dy)["io"].mean()
    t0 = _treasury(cfg).mean()
    hedge = -dv_io / (_treasury(cfg, -dy).mean() - _treasury(cfg, dy).mean())   # Treasuries (face 100) per IO
    gains = []
    for s in shifts:
        io = strip_paths(cfg, truth, shift=s)["io"].mean()
        gains.append(side * (io - price + hedge * (_treasury(cfg, s).mean() - t0)) / price * 100)
    return {"price": float(price), "hedge": float(side * hedge), "gain": np.array(gains)}


def coupon_stack(cfg: MbsConfig, market: PrepayModel, view: PrepayModel, wacs) -> list[dict]:
    """For each borrowers' rate: the market model's price at the market OAS, the OAS the view model needs to return
    that price, and the market model's effective duration."""
    out = []
    for w in wacs:
        m = strip_paths(cfg, market, w)
        price = float(m["pt"].mean())
        v = strip_paths(cfg, view, w)
        oas_view = solve_oas(price, v["flows"], v["rs"])
        up = strip_paths(cfg, market, w, shift=0.0025)["pt"].mean()
        dn = strip_paths(cfg, market, w, shift=-0.0025)["pt"].mean()
        dur = float((dn - up) / (2 * price * 0.0025))
        out.append({"wac": w, "price": price, "oas_view": oas_view, "duration": dur})
    return out


def tranche_rv(p: float = 0.06, rho_market: float = 0.30, rho_true: float = 0.15, attach: float = 0.03,
               detach: float = 0.07, recovery: float = 0.40, names: int = 125, trials: int = 4000,
               seed: int = 163) -> dict:
    """Expected loss of [attach, detach] at both correlations (share of the tranche); selling protection at the
    market's expected loss earns it and pays the loss realised on pools simulated at the true correlation."""
    el_m = expected_tranche_loss(attach, detach, p, rho_market, recovery)
    el_t = expected_tranche_loss(attach, detach, p, rho_true, recovery)
    losses = np.array([tranche_loss(x, attach, detach) for x in simulate_pool(names, p, rho_true, recovery, trials,
                                                                               seed)])
    pnl = el_m - losses
    return {"el_market": el_m, "el_true": el_t, "pnl_mean": float(pnl.mean()), "pnl_q05": float(np.quantile(pnl, 0.05)),
            "p_loss": float((pnl < 0).mean()), "wipeout": float((losses >= 1.0).mean())}
