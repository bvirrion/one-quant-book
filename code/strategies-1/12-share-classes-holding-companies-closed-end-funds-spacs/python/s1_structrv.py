"""Share classes, holding companies, closed-end funds and SPACs (One Quant Book 8, chapter 12).

Monte Carlo of the structural trades, 10,000 paths each. A closed-end fund at 85 cents on the dollar (a log discount
of -16.3%) whose discount reverts toward -10.5% (90 cents) with a half-life of two years and a volatility of 8% a
year, bought and hedged by shorting its portfolio, with carry of 1.3% a year (the fund's expenses and the hedge's
borrow), closed when the discount reaches 5% or after three years; with no catalyst, and with catalysts (a tender or a
liquidation that brings the discount to 2%) arriving at 0.1 or 0.3 a year. A holding company at 70 cents on the dollar
whose discount reverts to 80 cents with a half-life of three years, no catalyst. A SPAC bought at $9.80 against a
trust of $10.00 earning 4% a year, with the vote a year away, when the merged company's value per share is lognormal
with a median of $7 and a volatility of 60%. NumPy only.
"""
from __future__ import annotations

import functools
import math
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "structrv"))
from firm_structrv import discount_trade, simulate_discount, spac_return  # noqa: E402

YEAR, HORIZON, CARRY, PATHS = 252, 756, 0.013, 10000


@functools.lru_cache(maxsize=8)
def fund(catalyst_rate: float = 0.0, d0: float = math.log(0.85), mean: float = math.log(0.90),
         half_life: float = 504.0, close: float = math.log(0.95)):
    D, cat = simulate_discount(d0, mean, half_life, 0.08, HORIZON, catalyst_rate, math.log(0.98), PATHS,
                               np.random.default_rng(12))
    ret, day = discount_trade(D, cat, close, CARRY, HORIZON)
    years = day / YEAR
    return {"mean": float(ret.mean()), "ann": float(ret.mean() / years.mean()), "median_years": float(np.median(years)),
            "closed": float((day < HORIZON).mean()), "catalyst": float(((cat > 0) & (cat <= day)).mean()),
            "p5": float(np.percentile(ret, 5)), "loss": float((ret < 0).mean()), "ret": ret, "years": years}


def holding():
    return fund(0.0, math.log(0.70), math.log(0.80), 756.0, math.log(0.95))


@functools.lru_cache(maxsize=1)
def spac(price: float = 9.80, trust: float = 10.00, rate: float = 0.04, days: int = 252, median: float = 7.0,
         vol: float = 0.60):
    rng = np.random.default_rng(13)
    merged = median * np.exp(vol * rng.standard_normal(PATHS))
    r = spac_return(price, trust, rate, days, merged)
    floor = trust * math.exp(rate * days / 252) / price - 1
    hold = merged / price - 1
    return {"mean": float(r.mean()), "floor": float(floor), "redeem": float((merged < trust * math.exp(rate)).mean()),
            "hold_mean": float(hold.mean()), "hold_median": float(np.median(hold)), "ret": r}
