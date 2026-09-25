"""firm.qis -- quantitative investment strategies: index selection, fees and live against backtest (Book 9, ch. 27).

A bank's product team designs candidate rules-based indices (variants of a few strategies, so their backtests are
correlated), backtests them over ten years, launches the best, charges fees and hedges the swaps it sells, then lives
with five years of out-of-sample returns. Each candidate has a true annual Sharpe ratio; its estimated Sharpe ratio
over T years has sampling error of standard deviation 1 / sqrt(T) (normal daily returns), correlated across
candidates. Many independent teams give the distribution of the gap between the launched indices' backtests and their
live results, which the deflated Sharpe ratio (Book 4's `firm_multitest`) is meant to predict. A daily path of one
team's index illustrates it. NumPy only.

API (stable):
    QISConfig(...)                             parameters (seed 193)
    simulate_teams(cfg)                        true, backtest and live Sharpe ratios, (teams, candidates)
    launch(sim, cfg, k)                        the k best backtests per team: backtest, live gross and net Sharpe ratios
    deflated(sim, cfg)                         each team's best: deflated Sharpe probability; live results by verdict
    example_path(cfg, team)                    daily returns of one team's launched index, backtest then live
"""
from __future__ import annotations

import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "multitest"))
from firm_multitest import deflated_sharpe, expected_max_sr  # noqa: E402

YEAR = 252


@dataclass(frozen=True)
class QISConfig:
    teams: int = 2000
    candidates: int = 20
    seed: int = 193
    sr_mean: float = 0.10         # true annual Sharpe ratios of candidates: mean (median decay near 73%) ...
    sr_sd: float = 0.15           # ... and dispersion
    corr: float = 0.5             # correlation of candidates' estimation errors (variants of the same ideas)
    backtest_years: float = 10.0
    live_years: float = 5.0
    vol: float = 0.10             # index volatility target
    fee: float = 0.005            # index and swap fees a year
    leakage: float = 0.002        # cost of predictable rebalancing a year, borne live only


def simulate_teams(cfg: QISConfig | None = None) -> dict:
    cfg = cfg or QISConfig()
    rng = np.random.default_rng(cfg.seed)
    n, k = cfg.teams, cfg.candidates
    true = cfg.sr_mean + cfg.sr_sd * rng.standard_normal((n, k))

    def noise(years):
        common = rng.standard_normal((n, 1))
        own = rng.standard_normal((n, k))
        return (math.sqrt(cfg.corr) * common + math.sqrt(1 - cfg.corr) * own) / math.sqrt(years)

    return {"true": true, "backtest": true + noise(cfg.backtest_years), "live": true + noise(cfg.live_years)}


def launch(sim: dict, cfg: QISConfig | None = None, k: int = 3) -> dict:
    """Launch each team's k best backtests. Live net Sharpe ratio: gross less (fees + leakage) / vol."""
    cfg = cfg or QISConfig()
    order = np.argsort(-sim["backtest"], axis=1)[:, :k]
    pick = lambda a: np.take_along_axis(a, order, axis=1)  # noqa: E731
    bt, live, true = pick(sim["backtest"]), pick(sim["live"]), pick(sim["true"])
    net = live - (cfg.fee + cfg.leakage) / cfg.vol
    return {"backtest": bt, "true": true, "live": live, "net": net,
            "decay_median": float(np.median(1 - net / bt)), "gap": float((bt - net).mean())}


def deflated(sim: dict, cfg: QISConfig | None = None, threshold: float = 0.95) -> dict:
    """Deflated Sharpe probability of each team's best backtest, with the number of candidates as trials and the
    cross-sectional variance of the team's backtest Sharpe ratios; live results of those that pass and fail."""
    cfg = cfg or QISConfig()
    n_obs = int(cfg.backtest_years * YEAR)
    best = sim["backtest"].argmax(axis=1)
    rows = np.arange(len(best))
    sr_bt = sim["backtest"][rows, best]
    live = sim["live"][rows, best]
    p = np.empty(len(best))
    for i in rows:
        var = sim["backtest"][i].var(ddof=1) / YEAR                       # per-period Sharpe ratio variance
        sr0 = expected_max_sr(cfg.candidates, var)
        p[i] = deflated_sharpe(sr_bt[i] / math.sqrt(YEAR), n_obs, sr0=sr0)
    ok = p > threshold
    return {"prob": p, "pass": float(ok.mean()), "live_pass": float(live[ok].mean()) if ok.any() else float("nan"),
            "live_fail": float(live[~ok].mean()), "bt_pass": float(sr_bt[ok].mean()) if ok.any() else float("nan"),
            "bt_fail": float(sr_bt[~ok].mean())}


def example_path(cfg: QISConfig | None = None, team: int = 0) -> dict:
    """Daily returns (at the volatility target) of one team's launched index, backtest then live, drawn so that their
    annual Sharpe ratios over each period equal the simulated estimates."""
    cfg = cfg or QISConfig()
    sim = simulate_teams(cfg)
    j = int(sim["backtest"][team].argmax())
    rng = np.random.default_rng(cfg.seed + 1 + team)
    out = []
    for sr, years, cost in ((sim["backtest"][team, j], cfg.backtest_years, 0.0),
                            (sim["live"][team, j], cfg.live_years, cfg.fee + cfg.leakage)):
        n = int(years * YEAR)
        z = rng.standard_normal(n)
        z = (z - z.mean()) / z.std()
        d = cfg.vol / math.sqrt(YEAR)
        out.append(d * z + sr * cfg.vol / YEAR - cost / YEAR)
    return {"backtest": out[0], "live": out[1], "sr_backtest": float(sim["backtest"][team, j]),
            "sr_live": float(sim["live"][team, j])}
