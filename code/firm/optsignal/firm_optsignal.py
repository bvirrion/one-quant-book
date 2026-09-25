"""firm.optsignal -- an options layer and option-implied signals for stocks (build of One Quant Book 8, chapter 15).

For each stock and day: an at-the-money implied volatility (its realised volatility plus a premium and noise), an
out-of-the-money put and call implied volatility (a skew plus noise), and the ratio of option to stock volume. Informed
traders who know a coming surprise buy options in its direction during the days before the announcement: puts for bad
news (weighted more, because shorting the stock is costlier than buying a put) and calls for good; their demand raises
the implied volatility of the options they buy and the option volume. Signals: the skew (put minus at-the-money), the
volatility spread (call minus put), the option-to-stock volume ratio, and implied minus realised volatility. NumPy only.

API (stable):
    OptionConfig(...)                            parameters of the layer
    simulate_options(flag, surprise, listed, rv, cfg, rng)
                                                 {'atm', 'put', 'call', 'os'} (T, N) arrays
    signals(opt, rv)                             {'skew', 'spread', 'os', 'ivrv'}
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class OptionConfig:
    premium: float = 0.02              # at-the-money implied minus realised volatility, on average
    noise: float = 0.01                # daily noise of each implied volatility
    skew: float = 0.03                 # out-of-the-money put minus at-the-money volatility, on average
    window: int = 10                   # days before an announcement in which informed traders buy options
    impact: float = 0.003              # implied-volatility rise per unit of informed demand (one s.d. of surprise)
    os_base: float = 0.10              # option-to-stock volume ratio, median
    os_noise: float = 0.30             # its log noise
    os_impact: float = 0.15            # log rise of the ratio per unit of informed demand
    bad_news: float = 1.5              # informed demand for bad news relative to good (short-sale costs)
    seed: int = 15


def simulate_options(flag, surprise, listed, rv, cfg: OptionConfig | None = None, rng=None):
    cfg = cfg or OptionConfig()
    rng = rng or np.random.default_rng(cfg.seed)
    flag, listed = np.asarray(flag, bool), np.asarray(listed, bool)
    s = np.where(flag, np.nan_to_num(np.asarray(surprise, float)), 0.0)
    T, N = s.shape
    demand = np.zeros((T, N))                     # informed demand on day t: the surprise of an event within the window
    for k in range(1, cfg.window + 1):
        demand[:-k] += s[k:]
    weight = np.where(demand < 0, cfg.bad_news, 1.0)
    d = demand * weight
    atm = rv + cfg.premium + cfg.noise * rng.standard_normal((T, N))
    put = atm + cfg.skew + cfg.noise * rng.standard_normal((T, N)) + cfg.impact * np.maximum(-d, 0.0)
    call = atm + cfg.noise * rng.standard_normal((T, N)) + cfg.impact * np.maximum(d, 0.0)
    os_ = cfg.os_base * np.exp(cfg.os_noise * rng.standard_normal((T, N)) + cfg.os_impact * np.abs(d))
    mask = lambda x: np.where(listed, x, np.nan)  # noqa: E731
    return {"atm": mask(atm), "put": mask(put), "call": mask(call), "os": mask(os_)}


def signals(opt, rv):
    return {"skew": opt["put"] - opt["atm"], "spread": opt["call"] - opt["put"], "os": np.log(opt["os"]),
            "ivrv": opt["atm"] - rv}
