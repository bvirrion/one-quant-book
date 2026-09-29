"""firm.treasury -- house margin rules as data, the allocation of a book across brokers, and the cash and collateral
forecast with its survival horizon (build of One Quant Book 16, chapter 14).

A broker's house margin on the positions it holds is linear in three terms: a rate on the gross, a rate on the
absolute net, and a concentration add-on on the part of each position above a cap. Financing is a spread a year on
longs and a fee on shorts. `optimise` allocates each position across brokers (fractions summing to one) to minimise
the annual cost of the margin (at the firm's cost of cash) plus financing: a linear programme (scipy linprog), with
auxiliary variables for the absolute net and the concentration excesses. A clearing broker's futures margin comes
from firm.initmargin's filtered historical simulation.

The forecast: each account holds equity E (collateral); each day it gains the account's P&L and faces a requirement
m. A shortfall is a call paid from cash the same day; an excess is returned to cash unless the broker retains it.
A margin lock-up fixes a broker's house-margin terms for a notice period: `house_path` holds the multiplier at one
until the notice ends. The survival horizon is the first day cash falls below zero.

API (stable):
    Broker(name, gross, net, conc_cap, conc_rate, fin_long_bp, fin_short_bp)
    margin(broker, pos) ; financing(broker, pos) ; annual_cost(brokers, alloc, pos, r_cash)
    optimise(brokers, pos, r_cash) -> alloc (positions x brokers)
    fcm_margin(history, notional, h, q) ; house_path(multiplier, notice_days)
    forecast(cash0, equity0, pnl, req, retained, daily_cost)
    survival_horizon(cash) ; buffer_needed(cash)
"""
import pathlib
import sys
from dataclasses import dataclass

import numpy as np
from scipy.optimize import linprog

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "initmargin"))
import firm_initmargin as im  # noqa: E402


@dataclass(frozen=True)
class Broker:
    name: str
    gross: float            # margin per unit of gross exposure
    net: float              # margin per unit of absolute net exposure
    conc_cap: float         # position size above which the add-on applies
    conc_rate: float        # add-on per unit above the cap
    fin_long_bp: float      # financing spread on longs, bp a year
    fin_short_bp: float     # borrow and financing fee on shorts, bp a year


def margin(b, pos):
    pos = np.asarray(pos, float)
    conc = np.maximum(np.abs(pos) - b.conc_cap, 0.0).sum()
    return float(b.gross * np.abs(pos).sum() + b.net * abs(pos.sum()) + b.conc_rate * conc)


def financing(b, pos):
    pos = np.asarray(pos, float)
    return float((b.fin_long_bp * pos[pos > 0].sum() - b.fin_short_bp * pos[pos < 0].sum()) * 1e-4)


def annual_cost(brokers, alloc, pos, r_cash):
    pos = np.asarray(pos, float)
    return sum(r_cash * margin(b, pos * alloc[:, j]) + financing(b, pos * alloc[:, j]) for j, b in enumerate(brokers))


def optimise(brokers, pos, r_cash):
    p = np.asarray(pos, float)
    n, k = len(p), len(brokers)
    nx, nt = n * k, k                       # x[i, j] row-major, then t[j], then u[i, j]
    nv = nx + nt + nx
    c = np.zeros(nv)
    a_ub, b_ub, a_eq, b_eq = [], [], [], []
    for j, b in enumerate(brokers):
        c[nx + j] = r_cash * b.net
        for i in range(n):
            fin = (b.fin_long_bp if p[i] > 0 else b.fin_short_bp) * 1e-4 * abs(p[i])
            c[i * k + j] = r_cash * b.gross * abs(p[i]) + fin
            c[nx + nt + i * k + j] = r_cash * b.conc_rate
            row = np.zeros(nv)                  # |p| x - u <= cap
            row[i * k + j], row[nx + nt + i * k + j] = abs(p[i]), -1.0
            a_ub.append(row)
            b_ub.append(b.conc_cap)
        for sgn in (1.0, -1.0):                 # +-sum p x - t <= 0
            row = np.zeros(nv)
            for i in range(n):
                row[i * k + j] = sgn * p[i]
            row[nx + j] = -1.0
            a_ub.append(row)
            b_ub.append(0.0)
    for i in range(n):
        row = np.zeros(nv)
        row[i * k:(i + 1) * k] = 1.0
        a_eq.append(row)
        b_eq.append(1.0)
    bounds = [(0, 1)] * nx + [(0, None)] * (nt + nx)
    res = linprog(c, A_ub=np.array(a_ub), b_ub=b_ub, A_eq=np.array(a_eq), b_eq=b_eq, bounds=bounds, method="highs")
    if not res.success:
        raise RuntimeError(res.message)
    return res.x[:nx].reshape(n, k)


def fcm_margin(history, notional, h=2, q=0.99):
    """Initial margin on a futures position: filtered historical simulation of h-day moves (firm.initmargin)."""
    moves = im.fhs_moves(np.asarray(history, float).reshape(-1, 1), h)[:, 0]
    return im.hs_im(notional * moves, q)


def house_path(multiplier, notice_days):
    """A broker's house-margin multiplier as it applies to the firm: one during a lock-up's notice period."""
    m = np.asarray(multiplier, float).copy()
    m[:notice_days] = 1.0
    return m


def forecast(cash0, equity0, pnl, req, retained, daily_cost=0.0):
    """cash0: unencumbered cash; equity0[b]; pnl[t, b] and req[t, b] per day and account; retained[b] True if the
    broker keeps the account's excess. Returns (cash path, calls path, retained excess path)."""
    e = np.array(equity0, float)
    pnl, req = np.asarray(pnl, float), np.asarray(req, float)
    cash, calls, stuck = [], [], []
    c = float(cash0)
    for t in range(pnl.shape[0]):
        e += pnl[t]
        short = np.maximum(req[t] - e, 0.0)
        excess = np.maximum(e - req[t], 0.0)
        free = np.where(retained, 0.0, excess)
        c += free.sum() - short.sum() - daily_cost
        e += short - free
        cash.append(c)
        calls.append(short.sum())
        stuck.append(float(np.where(retained, excess, 0.0).sum()))
    return np.array(cash), np.array(calls), np.array(stuck)


def survival_horizon(cash):
    """Days until unencumbered cash first goes negative (len(cash) + 1 if it never does)."""
    neg = np.nonzero(np.asarray(cash) < 0)[0]
    return int(neg[0]) + 1 if len(neg) else len(cash) + 1


def buffer_needed(cash):
    """The extra starting cash that keeps the path non-negative."""
    return max(0.0, -float(np.min(cash)))
