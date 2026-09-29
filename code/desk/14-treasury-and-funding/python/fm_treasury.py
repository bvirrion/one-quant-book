"""One Quant Book 16, chapter 14: three prime brokers, a clearing broker and a bad week (illustrative, $ million).

An equity long-short book of five longs and five shorts, hedged with a short index future at a clearing broker.
Three prime brokers with different house-margin rules and financing spreads; the firm's cost of cash is 5 per cent.
"""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/treasury"))
import firm_treasury as tr  # noqa: E402

POS = np.array([120.0, 90.0, 80.0, 60.0, 40.0, -100.0, -85.0, -70.0, -45.0, -30.0])
FUT = -60.0
R_CASH = 0.05
BROKERS = [tr.Broker("A", 0.04, 0.25, 60.0, 0.15, 55.0, 35.0),
           tr.Broker("B", 0.10, 0.0, 1e9, 0.0, 40.0, 25.0),
           tr.Broker("C", 0.05, 0.15, 40.0, 0.30, 70.0, 30.0)]


def allocations():
    n, k = len(POS), len(BROKERS)
    out = {}
    for j, b in enumerate(BROKERS):
        a = np.zeros((n, k))
        a[:, j] = 1.0
        out[f"all at {b.name}"] = a
    out["pro rata"] = np.full((n, k), 1.0 / k)
    out["optimised"] = tr.optimise(BROKERS, POS, R_CASH)
    return out


def summary():
    rows = {}
    for name, a in allocations().items():
        m = [tr.margin(b, POS * a[:, j]) for j, b in enumerate(BROKERS)]
        fin = sum(tr.financing(b, POS * a[:, j]) for j, b in enumerate(BROKERS))
        rows[name] = {"margin": sum(m), "by_broker": m, "financing": fin,
                      "cost": tr.annual_cost(BROKERS, a, POS, R_CASH)}
    return rows


DAYS, CASH0, CUSHION = 30, 40.0, 0.10


def stress_returns():
    """Daily returns of longs, shorts and the index over thirty days: a five-day sell-off in which the shorts fall half
    as fast as the longs, a pause, a slow recovery."""
    r_long = np.r_[np.full(5, -0.02), np.zeros(5), np.full(20, 0.005)]
    r_short = np.r_[np.full(5, -0.01), np.zeros(5), np.full(20, 0.003)]
    r_idx = np.r_[np.full(5, -0.02), np.zeros(5), np.full(20, 0.004)]
    return r_long, r_short, r_idx


def house_multiplier():
    """Brokers raise house margin by a fifth a day to double in the sell-off, hold it, then ease to 1.5."""
    t = np.arange(1, DAYS + 1)
    return np.where(t <= 5, 1 + 0.2 * t, np.where(t <= 15, 2.0, 1.5))


def index_history(seed=14, n=500, vol=0.01):
    return np.random.default_rng(seed).normal(0.0, vol, n)


def paths(stress=True, alloc=None, notice=0):
    """Daily P&L and requirements for the three PB accounts and the clearing broker."""
    a = allocations()["optimised"] if alloc is None else alloc
    k = len(BROKERS)
    rl, rs, ri = stress_returns() if stress else (np.zeros(DAYS),) * 3
    mult = tr.house_path(house_multiplier(), notice) if stress else np.ones(DAYS)
    hist = index_history()
    pos, fut = POS.copy(), FUT
    pnl, req = np.zeros((DAYS, k + 1)), np.zeros((DAYS, k + 1))
    for t in range(DAYS):
        r = np.where(POS > 0, rl[t], rs[t])
        for j in range(k):
            pnl[t, j] = float((pos * a[:, j] * r).sum())
        pnl[t, k] = fut * ri[t]
        pos, fut = pos * (1 + r), fut * (1 + ri[t])
        hist = np.r_[hist, ri[t]]
        for j, b in enumerate(BROKERS):
            req[t, j] = mult[t] * tr.margin(b, pos * a[:, j])
        req[t, k] = tr.fcm_margin(hist, fut)
    return pnl, req


def initial(alloc=None):
    a = allocations()["optimised"] if alloc is None else alloc
    m = [tr.margin(b, POS * a[:, j]) for j, b in enumerate(BROKERS)]
    return np.array([x * (1 + CUSHION) for x in m] + [tr.fcm_margin(index_history(), FUT)])


def run(stress=True, notice=0, alloc=None, cash0=CASH0):
    """notice: days of margin lock-up (house terms fixed); 0 means the brokers may raise margin at once."""
    pnl, req = paths(stress, alloc, notice)
    a = allocations()["optimised"] if alloc is None else alloc
    daily = sum(tr.financing(b, POS * a[:, j]) for j, b in enumerate(BROKERS)) / 252
    retained = np.zeros(len(BROKERS) + 1, bool)
    cash, calls, stuck = tr.forecast(cash0, initial(alloc), pnl, req, retained, daily)
    return {"cash": cash, "calls": calls, "stuck": stuck, "horizon": tr.survival_horizon(cash),
            "buffer": tr.buffer_needed(cash), "min_cash": float(cash.min())}
