"""firm.teamtenure -- how long a platform team lasts under drawdown rules (build of One Quant Book 17, chapter 5).

A team runs capital with a true Sharpe ratio it does not know and an annual volatility (in fractions of its allocated
capital). The platform's ladder halves the team's capital when its drawdown from peak since hiring exceeds `cut` and
stops the team (it leaves) when the drawdown exceeds `stop`; drawdowns are measured on the capital actually run.
Teams that survive `years` are censored. From the simulated stop times the module estimates the survival curve
(Kaplan-Meier, which with censoring only at the horizon is the empirical survival function), the median tenure,
the annual turnover rate implied for a platform of such teams, and how many stopped teams were skilled.
Daily returns come from firm.podshop.pods (one call per team type), so the return model is Book 16's.

API (stable):
    Ladder(cut, stop)
    stop_times(sr, vol, ladder, n, years, rng, days=252) -> array of stop times in years (np.inf if never stopped)
    survival(times, grid) -> S(t) on the grid ; median_tenure(times) -> years or np.inf
    turnover(times, years) -> the annual rate at which teams leave, averaged over the horizon
    false_cut_share(times_by_sr, skilled) -> share of stopped teams whose true Sharpe ratio is in `skilled`
"""
import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "podshop"))
import firm_podshop as ps  # noqa: E402


@dataclass(frozen=True)
class Ladder:
    cut: float
    stop: float


def stop_times(sr, vol, ladder, n, years, rng, days=252):
    daily = ps.pods(n, years, sr, vol, 0.0, rng, days)["daily"]
    size = np.ones(n)
    eq = np.zeros(n)
    peak = np.zeros(n)
    out = np.full(n, np.inf)
    for t in range(daily.shape[0]):
        alive = np.isinf(out)
        eq += np.where(alive, size * daily[t], 0.0)
        peak = np.maximum(peak, eq)
        dd = peak - eq
        size = np.where(alive & (size == 1.0) & (dd > ladder.cut), 0.5, size)
        out = np.where(alive & (dd > ladder.stop), (t + 1) / days, out)
    return out


def survival(times, grid):
    t = np.asarray(times)
    return np.array([(t > g).mean() for g in grid])


def median_tenure(times):
    t = np.sort(np.asarray(times))
    k = math.ceil(len(t) / 2) - 1
    return float(t[k]) if len(t) % 2 else float(0.5 * (t[k] + t[k + 1]))


def turnover(times, years):
    """Leavers per team-year of exposure over the horizon (a constant-hazard reading of the curve)."""
    t = np.minimum(np.asarray(times), years)
    return float(np.isfinite(np.asarray(times)).sum() / t.sum())


def false_cut_share(times_by_sr, skilled):
    stopped = {sr: int(np.isfinite(t).sum()) for sr, t in times_by_sr.items()}
    total = sum(stopped.values())
    return sum(v for sr, v in stopped.items() if sr in skilled) / total if total else math.nan
