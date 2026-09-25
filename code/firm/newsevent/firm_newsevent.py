"""firm.newsevent -- a news stream and who captures its moves (build of One Quant Book 8, chapter 17).

News items arrive for stocks at random times in the trading day, each with a tone (the price move it will eventually
cause) and an attention level that falls with the number of other items the same day (investors distracted by other
news). A share of the move, larger with attention, is traded by machines within a fraction of a second after the item
(exponential with a time constant); the rest drifts in over the following days. Items moving the price by more than a
threshold halt the stock for a few minutes, and the immediate move happens at the reopening. NumPy only.

API (stable):
    NewsConfig(...)                              stream and reaction parameters
    simulate_news(days, stocks, cfg, rng)        structured array of items: day, second, stock, tone, attention, halted
    immediate_share(attention, cfg)              share of the move made within the day
    remaining(items, latency, cfg)               per item, the share of its move still ahead of a trader acting
                                                 `latency` seconds after the item (latency None: at the next close)
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class NewsConfig:
    per_day: float = 40.0              # news items a day across the market (Poisson)
    busy: float = 0.5                  # log spread of each day's news intensity (busy and quiet days)
    tone_sd: float = 0.02              # standard deviation of an item's total price move
    tau: float = 0.2                   # seconds: time constant of the machine reaction
    floor: float = 0.5                 # immediate share with no attention (one with full attention)
    distraction: float = 0.03          # attention falls as 1 / (1 + distraction x (items that day - 1))
    halt: float = 0.05                 # |tone| that halts the stock
    halt_seconds: float = 300.0
    session: float = 23400.0           # seconds in the trading day


def simulate_news(days: int, stocks: int, cfg: NewsConfig | None = None, rng=None):
    cfg = cfg or NewsConfig()
    rng = rng or np.random.default_rng(17)
    rows = []
    for d in range(days):
        k = rng.poisson(cfg.per_day * np.exp(cfg.busy * rng.standard_normal() - cfg.busy**2 / 2))
        if k == 0:
            continue
        att = np.full(k, 1.0 / (1.0 + cfg.distraction * (k - 1)))
        tone = cfg.tone_sd * rng.standard_normal(k)
        sec = rng.uniform(0, cfg.session, k)
        who = rng.integers(0, stocks, k)
        for j in range(k):
            rows.append((d, sec[j], who[j], tone[j], att[j], abs(tone[j]) > cfg.halt))
    dt = np.dtype([("day", int), ("second", float), ("stock", int), ("tone", float), ("attention", float),
                   ("halted", bool)])
    return np.array(rows, dtype=dt)


def immediate_share(attention, cfg: NewsConfig | None = None):
    cfg = cfg or NewsConfig()
    return cfg.floor + (1 - cfg.floor) * np.asarray(attention, float)


def remaining(items, latency, cfg: NewsConfig | None = None):
    cfg = cfg or NewsConfig()
    share = immediate_share(items["attention"], cfg)
    if latency is None:
        return 1 - share
    lat = float(latency)
    fast = np.exp(-lat / cfg.tau)
    fast = np.where(items["halted"], 0.0, fast)        # a halted stock reopens at the new price: nothing to catch
    return share * fast + (1 - share)
