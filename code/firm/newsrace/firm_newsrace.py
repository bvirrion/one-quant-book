"""firm.newsrace -- scheduled releases, the race, and a market maker's event protocol (One Quant Book 11, chapter 18).

A number is released at t = 0. Its surprise z (standard normal) moves a future's fair value by J = round(beta * z)
ticks. Quotes that were resting before the release are stale until their owners react: the other liquidity providers
update after `stale_ms` milliseconds. Traders in latency tiers take every stale quote between the old price and the
new one, fastest first, each tier up to its capacity; a lot taken k ticks from the old price earns J - k ticks. Our
market maker rests `mm_lots` at each of the first levels unless its event protocol pulls them before the release; the
protocol then re-enters after `reenter_s` seconds into post-release flow whose volume and toxicity decay.

The chapter's news stream for unscheduled items is Book 8's firm.newsevent; this module is for scheduled numbers.

API (stable):
    move(z, beta)                                   J in ticks
    race(J, stale_lots, tiers, stale_ms)            tick-lots captured by each tier, and the lots taken per level
    mm_loss(J, mm_lots, other_lots, tiers, stale_ms)
                                                    the market maker's loss (tick-lots) if it leaves its quotes
    reentry(t, lam0, boost, decay_s, half_spread, adverse0, adverse_decay_s, horizon_s, dt)
                                                    expected spread less mark-outs (tick-lots) from quoting after t
    simulate(n, seed, beta, ...) -> dict            per-tier share of the captured move, the market maker's mean loss
                                                    with and without the protocol, and the best re-entry time
    misparse(p_wrong, capture_right, loss_wrong)    expected value of trading a machine-read headline
"""
from __future__ import annotations

import numpy as np


def move(z: float, beta: float = 3.0) -> int:
    return int(np.round(beta * z))


def race(J: int, stale_lots, tiers, stale_ms: float) -> tuple[np.ndarray, np.ndarray]:
    """stale_lots[k] is the lots resting k+1 ticks from the old price on the side the move takes out. tiers: list of
    (latency_ms, capacity_lots). Returns the tick-lots each tier captures and the lots taken at each level."""
    J = abs(J)
    left = np.array(stale_lots, float)
    taken = np.zeros_like(left)
    got = np.zeros(len(tiers))
    order = sorted(range(len(tiers)), key=lambda i: tiers[i][0])
    for i in order:
        lat, cap = tiers[i]
        if lat >= stale_ms:
            continue
        for k in range(min(J - 1, len(left))):          # levels strictly inside the move are worth taking
            q = min(cap, left[k])
            got[i] += q * (J - (k + 1))
            left[k] -= q
            taken[k] += q
            cap -= q
            if cap <= 0:
                break
    return got, taken


def mm_loss(J: int, mm_lots, other_lots, tiers, stale_ms: float) -> float:
    """Our lots rest at the back of each level's queue (the others were there first); takers consume a level from
    the front. Loss: for each lot of ours taken at level k, J - k ticks."""
    mm_lots, other_lots = np.asarray(mm_lots, float), np.asarray(other_lots, float)
    _, taken = race(J, mm_lots + other_lots, tiers, stale_ms)
    ours = np.clip(taken - other_lots, 0.0, mm_lots)
    k = np.arange(1, len(mm_lots) + 1)
    return float(np.sum(ours * np.maximum(abs(J) - k, 0)))


def reentry(t: float, lam0: float = 2.0, boost: float = 20.0, decay_s: float = 30.0, half_spread: float = 1.0,
            adverse0: float = 3.0, adverse_decay_s: float = 5.0, horizon_s: float = 120.0, dt: float = 0.05) -> float:
    """Quote from t to the horizon: fills at rate lam0 (1 + boost e^{-s/decay}) lots a second, each earning the
    half-spread less a mark-out adverse0 e^{-s/adverse_decay} (ticks)."""
    s = np.arange(t, horizon_s, dt)
    rate = lam0 * (1.0 + boost * np.exp(-s / decay_s))
    edge = half_spread - adverse0 * np.exp(-s / adverse_decay_s)
    return float(np.sum(rate * edge) * dt)


def simulate(n: int = 20000, seed: int = 0, beta: float = 3.0, levels: int = 10, other_lots: float = 50.0,
             mm_lots: float = 20.0, mm_levels: int = 3, stale_ms: float = 20.0,
             tiers=((0.05, 200.0), (1.0, 200.0), (5.0, 200.0), (50.0, 200.0)), reenter_grid=(0.5, 1, 2, 5, 10, 20, 40)):
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(n)
    other = np.full(levels, other_lots)
    mm = np.zeros(levels)
    mm[:mm_levels] = mm_lots
    got = np.zeros(len(tiers))
    loss = 0.0
    total_move = 0.0
    for zi in z:
        J = move(zi, beta)
        if abs(J) < 2:
            continue
        g, _ = race(J, mm + other, tiers, stale_ms)
        got += g
        total_move += g.sum()
        loss += mm_loss(J, mm, other, tiers, stale_ms)
    re = {t: reentry(t) for t in reenter_grid}
    best = max(re, key=re.get)
    return {"share": got / total_move if total_move else got, "captured_per_release": total_move / n,
            "mm_loss_per_release": loss / n, "reentry": re, "best_reentry": best, "tiers": tiers}


def misparse(p_wrong: float, capture_right: float, loss_wrong: float) -> float:
    return (1.0 - p_wrong) * capture_right - p_wrong * loss_wrong
