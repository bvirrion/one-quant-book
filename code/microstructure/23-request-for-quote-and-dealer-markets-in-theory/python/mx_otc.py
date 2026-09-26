"""One Quant Book 10, chapter 23: search, requests for quote and dealer networks.

    DGP, dgp_study()        the dealer market's steady state and spread as the investors' contact rate with dealers
                            rises (meetings a year)
    RFQ, rfq_study()        the client's expected cost of selling a bond to the best of n dealers against n, for several
                            leakage costs per losing dealer, and the cost-minimising n
    common_study()          the same optimum with and without a common-value part in the dealers' estimates
    chase_study()           spreads to uninformed and informed clients as the value of an informed trade's information
                            to the dealer rises
    network_study()         a core-periphery network (10 core dealers, 200 peripheral ones with two core links each):
                            intermediation chains and markups by the type of the buyer's dealer
All deterministic (fixed seeds).
"""
from __future__ import annotations

import functools
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("otcsearch", "rfq"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_otcsearch import best_n, chase, core_periphery, dgp, intermediation, rfq_cost, rfq_simulate  # noqa: E402

DGP = dict(lam_u=2.0, lam_d=0.2, s=0.8, r=0.05, delta=2.0, z=0.8)
RHOS = (10.0, 30.0, 100.0, 300.0, 1000.0)


@functools.cache
def dgp_study() -> dict:
    return {rho: dgp(rho=rho, **DGP) for rho in RHOS}


RFQ = dict(markup=10.0, sigma_p=5.0, sigma_c=2.0)
LEAKS = (0.1, 0.25, 0.5, 1.0, 2.0, 3.0)
NS = tuple(range(1, 13))


@functools.cache
def rfq_study() -> dict:
    out = {}
    for leak in LEAKS:
        n = best_n(leak=leak, **RFQ)
        out[leak] = {"best_n": n, "cost": rfq_cost(n, leak=leak, **RFQ),
                     "curve": [rfq_cost(k, leak=leak, **RFQ) for k in NS]}
    out["check"] = (rfq_simulate(5, leak=0.5, trials=200_000, **RFQ), rfq_cost(5, leak=0.5, **RFQ))
    return out


@functools.cache
def common_study(leak: float = 0.5) -> dict:
    p = RFQ["sigma_p"]
    return {sc: {"best_n": best_n(RFQ["markup"], p, sc, leak), "cost": rfq_cost(best_n(RFQ["markup"], p, sc, leak),
                                                                              RFQ["markup"], p, sc, leak)}
            for sc in (0.0, 2.0, 5.0)}


INFO = (0.0, 1.0, 1.5, 2.0, 3.0)


@functools.cache
def chase_study(cost: float = 2.0, adverse: float = 1.5) -> dict:
    return {v: chase(cost, adverse, v) for v in INFO}


@functools.cache
def network_study() -> dict:
    adj = core_periphery(10, 200, 2, seed=23)
    return intermediation(adj, 10, 4.0, 2.0, trials=20_000, seed=5)
