"""Quantitative investment strategies (One Quant Book 9, chapter 27).

Synthetic: firm.qis's 2,000 product teams, each backtesting 20 correlated candidate indices over ten years and living
with five years after launch; true Sharpe ratios drawn around 0.10 (sd 0.15), calibrated so the median decay from
backtest to live net Sharpe ratio is near the 73% reported for bank-built strategies; fees of 0.5% and rebalancing
leakage of 0.2% a year at a 10% volatility target; the deflated Sharpe ratio's verdicts; the decay against the number
of candidates; and one team's launched index, backtest then live. NumPy.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "qis"))
from firm_qis import QISConfig, deflated, example_path, launch, simulate_teams  # noqa: E402

COUNTS = (2, 5, 10, 20, 50, 100)


@functools.lru_cache(maxsize=1)
def market():
    cfg = QISConfig()
    return cfg, simulate_teams(cfg)


def launched(k: int = 3) -> dict:
    """Means over the launched indices: backtest, true, live gross and live net Sharpe ratios; median decay; share of
    launched indices whose live net Sharpe ratio is negative."""
    cfg, sim = market()
    L = launch(sim, cfg, k)
    return {"backtest": float(L["backtest"].mean()), "true": float(L["true"].mean()), "live": float(L["live"].mean()),
            "net": float(L["net"].mean()), "decay": L["decay_median"], "negative": float((L["net"] < 0).mean()),
            "all_true": float(sim["true"].mean())}


def verdicts() -> dict:
    cfg, sim = market()
    d = deflated(sim, cfg)
    return {k: v for k, v in d.items() if k != "prob"}


def complexity() -> dict:
    """Median decay and mean backtest Sharpe ratio of each team's best, against the number of candidates."""
    out = {}
    for n in COUNTS:
        cfg = QISConfig(candidates=n)
        L = launch(simulate_teams(cfg), cfg, 1)
        out[n] = {"decay": L["decay_median"], "backtest": float(L["backtest"].mean()), "net": float(L["net"].mean())}
    return out


def path() -> dict:
    cfg = QISConfig()
    e = example_path(cfg, 0)
    return e | {"cum": np.cumsum(np.concatenate([e["backtest"], e["live"]])), "split": len(e["backtest"])}
