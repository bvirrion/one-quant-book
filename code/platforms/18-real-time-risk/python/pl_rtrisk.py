"""Real-time risk (One Quant Book 15, chapter 18).

An afternoon (13:00 to 17:30) of an index at 5,000 with seeded moves. Two desks trade it: desk A buys index puts
(six listed lines, priced by Book 5's library under Black-Scholes, 20% volatility, 4% rates), desk B sells index
futures. Each desk checks its own exposure before every trade and stays under 90% of its limit of $50 million of
delta; the firm's appetite is also $50 million. The executions go through firm.posservice, and a firm-level
aggregator (firm.rtrisk) adds everything up as it happens: the chapter measures when the firm's limit was breached
while both desks stayed inside theirs, the exposure at the close, and how far the market can move before the cached
sensitivities misstate the P&L of desk A's options by more than 1% of a full revaluation.
"""
from __future__ import annotations

import datetime as dt
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for p in ("code/firm/rtrisk", "code/firm/pricing", "code/firm/posservice"):
    sys.path.insert(0, str(ROOT / p))
import firm_posservice as PS  # noqa: E402
import firm_pricing as FP  # noqa: E402
import firm_rtrisk as RT  # noqa: E402

ASOF, S0, VOL, RATE = dt.date(2026, 9, 15), 5_000.0, 0.20, 0.04
START, END, TICK = 13 * 3600, 17 * 3600 + 1800, 10          # seconds since midnight
LIMIT, DESK_USE = 50e6, 0.9
PARENTS = {"firm": None, "desk A": "firm", "desk B": "firm", "A puts": "desk A", "B futures": "desk B"}
LIMITS = {"firm": LIMIT, "desk A": LIMIT, "desk B": LIMIT}
PUTS = [FP.EuropeanOption(id=f"IDX-P{k}-{m}", underlying="IDX", currency="USD", strike=k,
                          expiry=ASOF + dt.timedelta(days=30 * m), right="P")
        for k in (4_800, 4_900, 5_000) for m in (1, 2)]
FUT = RT.Future("IDX-FUT", "IDX")


def market(spot: float) -> FP.MarketData:
    return FP.MarketData(ASOF, {"IDX": spot}, {"USD": FP.FlatCurve(RATE, ASOF)}, vols={"IDX": FP.FlatVol(VOL)})


def path(seed: int = 18) -> np.ndarray:
    """The index every ten seconds: 20% annual volatility, a drift of -1.5% over the afternoon."""
    rng = np.random.default_rng(seed)
    n = (END - START) // TICK
    step = VOL * np.sqrt(TICK / (252 * 6.5 * 3600))
    return S0 * np.exp(np.cumsum(np.r_[0.0, -0.015 / n + step * rng.standard_normal(n)]))


def afternoon(seed: int = 18, threshold: float = 0.005) -> dict:
    rng = np.random.default_rng(seed + 1)
    s = path(seed)
    times = START + TICK * np.arange(len(s))
    agg = RT.Aggregator(RT.Hierarchy(PARENTS), RT.SensitivityCache(market(S0), "IDX", threshold), LIMITS)
    pos = PS.PositionService(("desk",))
    fills = {"desk A": [], "desk B": []}
    nxt = {"desk A": START + rng.exponential(300), "desk B": START + rng.exponential(300)}
    series = []
    n_exec = 0
    for t, spot in zip(times, s, strict=True):
        agg.on_tick(float(t), market(float(spot)))
        for desk in ("desk A", "desk B"):
            while nxt[desk] <= t:
                nxt[desk] += rng.exponential(300)
                if desk == "desk A":
                    inst, qty, book = PUTS[int(rng.integers(len(PUTS)))], 1_000.0, "A puts"
                else:
                    inst, qty, book = FUT, -400.0, "B futures"
                after, _ = agg.what_if(book, inst, qty)
                if abs(after[desk]) > DESK_USE * LIMITS[desk]:      # the desk's own check, on its own number
                    continue
                n_exec += 1
                side = 1 if qty > 0 else -1
                pos.on_execution("desk", PS.Execution(f"x{n_exec}", desk, inst.id, side, int(abs(qty)),
                                                      int(round(spot * 1e4)), int(t * 1e9), 0, 1))
                agg.on_fill(float(t), book, inst.id, inst, qty)
                fills[desk].append((float(t), inst.id, qty))
        series.append((float(t), float(spot), agg.exposure("firm"), agg.exposure("desk A"), agg.exposure("desk B")))
    firm_alert = next((a for a in agg.alerts if a[1] == "firm"), None)
    return {"series": np.array(series), "alerts": agg.alerts, "firm_alert": firm_alert, "agg": agg, "pos": pos,
            "fills": fills, "close_spot": float(s[-1]), "refreshes": agg.cache.refreshes}


def book_at_close(r: dict) -> list:
    """Desk A's options at the close: (instrument, quantity) from the position service."""
    out = []
    for inst in PUTS:
        q = r["pos"].position("desk A", inst.id).quantity
        if q:
            out.append((inst, float(q)))
    return out


MOVES = np.linspace(-0.10, 0.10, 81)


def approximation_error(r: dict, moves=MOVES) -> list[tuple]:
    """Delta-gamma P&L from sensitivities computed at the close, against full revaluation, per move."""
    s1 = r["close_spot"]
    md0 = market(s1)
    cache = RT.SensitivityCache(md0, "IDX")
    book = book_at_close(r)
    rows = []
    for x in moves:
        md1 = market(s1 * (1 + x))
        approx = sum(RT.delta_gamma_pnl(cache.greeks(i), q, s1, s1 * (1 + x)) for i, q in book)
        full = sum(RT.full_pnl(i, q, md0, md1) for i, q in book)
        rows.append((float(x), approx, full, abs(approx - full) / abs(full) if full else 0.0))
    return rows


def one_percent_move(rows) -> float:
    """The smallest absolute move at which the approximation's error exceeds 1% of the full revaluation."""
    bad = [abs(x) for x, _a, _f, e in rows if e > 0.01 and x != 0]
    return min(bad) if bad else float("nan")


def what_if_at_close(r: dict) -> dict:
    """Desk B asks, at the close, what selling 400 more futures would do."""
    after, breached = r["agg"].what_if("B futures", FUT, -400.0)
    return {"after": after, "breached": breached}
