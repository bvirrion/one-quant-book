"""firm.deltaone -- index arbitrage, financing trades and dividends from structured issuance (Book 9, chapter 26).

Index futures trade around their fair value (Book 1's `firm_fairvalue`): the basis they imply is the market's
financing rate for holding the basket, a spread over the overnight rate that mean-reverts and jumps at quarter-ends
when bank balance sheets are scarce. Short-lived mispricings around that fair value are index arbitrage; holding the
basket against a short future to expiry locks the implied spread, which a bank that funds itself more cheaply earns as
a financing trade. An issuer of autocallables (Book 5's `firm_autocall`) is left long dividends; in this chapter's
market, issuers' selling puts dividend futures below expected dividends, more so at longer maturities, and a buyer
holding them to expiry earns the discount while bearing dividend cuts in recessions. NumPy only.

API (stable):
    DeltaOneConfig(...)                         parameters (seed 191)
    simulate_financing(cfg)                     dict: daily implied financing spread; minute futures mispricing (bp)
    index_arb(sim, cfg, lag)                    trades fading the mispricing beyond the round-trip cost
    financing_trade(sim, cfg, offset)           quarterly basket-against-future trades held to expiry
    issuer_dividend_exposure(vol, r, q, bump)   change of an autocallable's value (per 100) for a rise in dividend yield
    dividend_market(cfg)                        dividend futures prices, realised dividends and holding returns
"""
from __future__ import annotations

import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "autocall"))
from firm_autocall import TermSheet, price  # noqa: E402

YEAR = 252
QUARTER = 63


@dataclass(frozen=True)
class DeltaOneConfig:
    days: int = 10 * YEAR
    seed: int = 191
    spread_mean: float = 20.0     # futures-implied financing over the overnight rate (bp a year) ...
    spread_sd: float = 12.0
    spread_hl: float = 40.0       # ... mean-reverting (days) ...
    quarter_end: float = 25.0     # ... plus this in the last 10 days of each quarter
    minutes: int = 390 * YEAR     # a year of minute observations for index arbitrage ...
    mis_sd: float = 4.0           # ... of the future's mispricing around fair value (bp of the index) ...
    mis_hl: float = 10.0          # ... reverting with this half-life (minutes)
    basket_cost: float = 2.0      # bp of notional per side for the basket (a bank crossing part of it internally)
    futures_cost: float = 0.5     # bp per side for the future
    own_funding: float = 10.0     # the bank's funding over the overnight rate (bp a year)
    capital_charge: float = 5.0   # balance-sheet charge (bp a year)
    years: int = 5                # dividend futures maturities 1..years
    div_level: float = 100.0      # expected dividends next year (index points)
    div_growth: float = 0.03
    discount: float = 0.04        # supply discount per year of maturity (share of expected dividends)
    div_vol: float = 0.06         # yearly dividend growth noise
    recession_p: float = 0.12     # chance of a recession year ...
    recession_cut: float = 0.30   # ... cutting that year's dividends by this share
    scenarios: int = 20_000


def _ou(rng, n, sd, hl):
    phi = 0.5 ** (1 / hl)
    x, e = np.empty(n), sd * math.sqrt(1 - phi * phi) * rng.standard_normal(n)
    x[0] = sd * rng.standard_normal()
    for t in range(1, n):
        x[t] = phi * x[t - 1] + e[t]
    return x


def simulate_financing(cfg: DeltaOneConfig | None = None) -> dict:
    cfg = cfg or DeltaOneConfig()
    rng = np.random.default_rng(cfg.seed)
    n = cfg.days
    qend = (np.arange(n) % QUARTER) >= QUARTER - 10
    spread = cfg.spread_mean + _ou(rng, n, cfg.spread_sd, cfg.spread_hl) + cfg.quarter_end * qend
    return {"spread": spread, "mispricing": _ou(rng, cfg.minutes, cfg.mis_sd, cfg.mis_hl), "quarter_end": qend}


def index_arb(sim: dict, cfg: DeltaOneConfig | None = None, lag: int = 1) -> dict:
    """Sell the future and buy the basket when the future is rich by more than the round-trip cost (the reverse when
    cheap); unwind when the mispricing crosses zero. Both legs execute `lag` observations after the signal, when part
    of the mispricing has gone. P&L per trade in bp of notional."""
    cfg = cfg or DeltaOneConfig()
    band = 2 * (cfg.basket_cost + cfg.futures_cost)
    m, pnl, pos, entry = sim["mispricing"], [], 0, 0.0
    for t in range(len(m) - lag):
        x = m[t]
        if pos == 0 and abs(x) > band:
            pos, entry = (-1 if x > 0 else 1), m[t + lag]
        elif pos != 0 and np.sign(x) != -pos:
            pnl.append(pos * (m[t + lag] - entry) - band)
            pos = 0
    return {"pnl": np.array(pnl), "band": band}


def financing_trade(sim: dict, cfg: DeltaOneConfig | None = None, offset: int = 0) -> dict:
    """Each quarter, `offset` days into it, buy the basket and sell a future expiring a quarter later, locking the
    implied spread; the bank pays its own funding and a capital charge, and the round-trip cost. P&L per trade in bp
    of notional; a trade is taken only when it is expected to pay."""
    cfg = cfg or DeltaOneConfig()
    cost = 2 * (cfg.basket_cost + cfg.futures_cost)
    locked = sim["spread"][offset::QUARTER]
    net = (locked - cfg.own_funding - cfg.capital_charge) * QUARTER / YEAR - cost
    take = net > 0
    return {"locked": locked, "net": net, "taken": take, "pnl": np.where(take, net, 0.0)}


def issuer_dividend_exposure(vol: float = 0.2, r: float = 0.03, q: float = 0.03, bump: float = 0.001,
                             n_paths: int = 40_000, seed: int = 18) -> dict:
    """A five-year annual-observation autocallable (trigger 100%, 8% Phoenix coupon at a 70% barrier, 60% protection
    at maturity). Value per 100 at q and q + bump with common random numbers: the issuer, short the note, gains when
    dividends rise."""
    ts = TermSheet(obs_times=(1.0, 2.0, 3.0, 4.0, 5.0), trigger=1.0, coupon=8.0, coupon_barrier=0.7, protection=0.6)
    lo = price(ts, lambda t, s: vol, r, q, n_paths, seed)
    hi = price(ts, lambda t, s: vol, r, q + bump, n_paths, seed)
    life = sum((j + 1) * p for j, p in enumerate(lo["call_probs"])) + 5.0 * lo["maturity_prob"]
    return {"price": lo["price"], "bumped": hi["price"], "issuer_gain": lo["price"] - hi["price"],
            "expected_life": life}


def dividend_market(cfg: DeltaOneConfig | None = None) -> dict:
    """Scenarios of the next `years` of dividends: growth noise and recession years that cut dividends and the index
    together. Futures for year y trade at expected dividends x (1 - discount x y). Holding returns to expiry."""
    cfg = cfg or DeltaOneConfig()
    rng = np.random.default_rng(cfg.seed + 1)
    n, Y = cfg.scenarios, cfg.years
    rec = rng.random((n, Y)) < cfg.recession_p
    cut = math.log(1 - cfg.recession_cut)
    g = cfg.div_growth - cut * cfg.recession_p + cfg.div_vol * rng.standard_normal((n, Y)) + cut * rec
    level = cfg.div_level / math.exp(cfg.div_growth) * np.exp(np.cumsum(g, axis=1))
    expected = level.mean(axis=0)
    years = np.arange(1, Y + 1)
    futures = expected * (1 - cfg.discount * years)
    ret = level / futures - 1
    equity = 0.06 + 0.15 * rng.standard_normal((n, Y)) - 0.25 * rec                  # the index in the same years
    return {"expected": expected, "futures": futures, "realised": level, "return": ret,
            "annual": (1 + ret) ** (1 / years) - 1, "recession": rec, "equity": equity}
