"""The valuation-adjustment desk's quote service (build of One Quant Book 6, chapter 20).

Over `firm_exposure` (values on common scenarios), `firm_cva` and `firm_xvafund`:
- incremental adjustments: the change in a netting set's adjustment when a trade is added;
- Euler allocation of a netting set's CVA to its trades: CVA is homogeneous of degree one in the trades'
  sizes, so CVA = sum_i a_i with a_i = (1 - R) sum_k E[D V_i 1{V > 0}](t_k) dPD_k (midpoint rule);
- proxy credit spreads for names without quotes: least squares of log spreads of liquid peers on
  credit-quality, sector and region indicators (the three variables the Basel CVA framework requires);
- the conversion of an upfront charge into a running spread on the trade.
"""
import math
import pathlib
import sys
from collections.abc import Callable, Sequence

import numpy as np

HERE = pathlib.Path(__file__).resolve().parents[1]
for comp in ("cva", "cdscurve", "exposure", "xvafund"):
    sys.path.insert(0, str(HERE / comp))
from firm_cdscurve import HazardCurve  # noqa: E402
from firm_cva import cva, discounted_profiles  # noqa: E402


def netting_cva(values: Sequence[np.ndarray], D: np.ndarray, times: np.ndarray, cpty: HazardCurve,
                recovery: float = 0.4) -> float:
    dee, _ = discounted_profiles(np.sum(values, axis=0), D)
    return cva(dee, times, cpty, recovery)


def incremental(adjustment: Callable[[list[np.ndarray]], float], existing: list[np.ndarray],
                new: np.ndarray) -> dict:
    """Standalone, incremental and existing-set values of any adjustment functional of trade values."""
    base = adjustment(existing)
    return {"base": base, "with": adjustment(existing + [new]), "standalone": adjustment([new]),
            "incremental": adjustment(existing + [new]) - base}


def euler_cva(values: Sequence[np.ndarray], D: np.ndarray, times: np.ndarray, cpty: HazardCurve,
              recovery: float = 0.4) -> list[float]:
    """Euler contributions of each trade to the netting set's CVA (they add up to the total)."""
    V = np.sum(values, axis=0)
    ind = (V > 0).astype(float)
    q = np.array([cpty.survival(float(t)) for t in times])
    dq = q[:-1] - q[1:]
    out = []
    for v in values:
        c = (D * v * ind).mean(axis=0)
        out.append(float((1.0 - recovery) * np.sum(0.5 * (c[1:] + c[:-1]) * dq)))
    return out


def proxy_spread(peers: Sequence[tuple[str, str, str, float]], target: tuple[str, str, str]) -> dict:
    """Fit log(spread) = a + rating + sector + region effects on peers; predict the target's spread."""
    cats = [sorted({p[i] for p in peers}) for i in range(3)]
    for i, c in enumerate(target):
        if c not in cats[i]:
            raise ValueError(f"no peer with {c}")

    def row(r):
        x = [1.0]
        for i in range(3):
            x += [1.0 if r[i] == c else 0.0 for c in cats[i][1:]]
        return x

    X = np.array([row(p) for p in peers])
    y = np.log([p[3] for p in peers])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    fit = X @ beta
    resid = y - fit
    return {"spread": float(math.exp(np.array(row(target)) @ beta)), "beta": beta,
            "rmse": float(math.sqrt(np.mean(resid ** 2)))}


def running_charge(upfront: float, notional: float, annuity: float) -> float:
    """Upfront adjustment as a running spread (decimal a year) on the trade's notional."""
    return upfront / (notional * annuity)
