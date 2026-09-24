"""Index reconstitution with buffers, passive demand and a stylised event path (Chapter 15). Illustrative."""
import math

import numpy as np


def ranks(caps: np.ndarray) -> np.ndarray:
    """Rank 1 = largest capitalisation."""
    order = np.argsort(-caps, kind="stable")
    out = np.empty(len(caps), dtype=int)
    out[order] = np.arange(1, len(caps) + 1)
    return out


def reconstitute(caps: np.ndarray, member: np.ndarray, n: int, buffer: int) -> np.ndarray:
    """Top-n index with a buffer: a member stays while ranked n + buffer or better; an outsider
    enters only when ranked n - buffer or better; remaining places are filled by rank."""
    rk = ranks(caps)
    keep = member & (rk <= n + buffer)
    enter = ~member & (rk <= n - buffer)
    new = keep | enter
    for i in np.argsort(rk):                     # fill, or trim, to exactly n names
        if new.sum() >= n:
            break
        new[i] = True
    for i in np.argsort(-rk):
        if new.sum() <= n:
            break
        if new[i] and not (member[i] and rk[i] <= n):
            new[i] = False
    return new


def one_way_turnover(caps: np.ndarray, old: np.ndarray, new: np.ndarray) -> float:
    """Weight of the additions in the new capitalisation-weighted index."""
    return float(caps[new & ~old].sum() / caps[new].sum())


def simulate_turnover(n_stocks: int, n: int, buffer: int, years: int, seed: int, vol: float = 0.35):
    rng = np.random.default_rng(seed)
    caps = np.exp(rng.normal(0.0, 1.5, n_stocks))
    member = ranks(caps) <= n
    names, weight = [], []
    for _ in range(years):
        caps = caps * np.exp(rng.normal(0.0, vol, n_stocks))
        new = reconstitute(caps, member, n, buffer)
        names.append(int((new & ~member).sum()))
        weight.append(one_way_turnover(caps, member, new))
        member = new
    return float(np.mean(names)), float(np.mean(weight))


def passive_demand(tracked_assets: float, index_cap: float, stock_float_cap: float) -> float:
    """Dollars that trackers must buy of an addition: tracked assets times its new weight."""
    return tracked_assets * stock_float_cap / index_cap


def adv_multiple(demand: float, adv_dollars: float) -> float:
    return demand / adv_dollars


def event_path(days_before: int, days_after: int, announce: int, permanent: float, temporary: float,
               half_life: float) -> np.ndarray:
    """Stylised cumulative abnormal return around an addition. Day 0 = effective date (close).
    A jump at the announcement, a linear run-up of the temporary part to day 0, then decay."""
    t = np.arange(-days_before, days_after + 1)
    car = np.zeros(len(t))
    for k, d in enumerate(t):
        if d < announce:
            continue
        if d <= 0:
            car[k] = permanent + temporary * (d - announce + 1) / (1 - announce)
        else:
            car[k] = permanent + temporary * math.exp(-math.log(2) * d / half_life)
    return car
