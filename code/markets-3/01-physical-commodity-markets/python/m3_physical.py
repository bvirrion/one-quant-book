"""Chapter 1 of Book 3: physical commodity markets. A refiner's cargo priced over five days around the
bill of lading and hedged with futures; a trading house's back-to-back cargo with mismatched pricing
periods; the WTI-Brent differential since 2000. Price dynamics are illustrative (random walks with
stated daily volatilities); the differential series is FRED data (EIA spot prices)."""
import csv
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/physdeal"))
from firm_physdeal import Leg, exposure, hedge_trades, locked_margin, pricing_days

DATA = pathlib.Path(__file__).resolve().parents[4] / "data/markets-3"
VOLUME = 700_000                 # barrels, one cargo
SIGMA_F = 1.80                   # daily volatility of the futures price, $/bbl (illustrative)
SIGMA_B = 0.12                   # daily volatility of the physical-minus-futures basis, $/bbl (illustrative)
F0, B0, DIFF = 80.0, -0.30, 0.40  # futures today, basis today, contract differential ($/bbl)
BL_DAY = 20                      # expected bill-of-lading day, business days from today


def simulate_cargo(n_paths: int = 20_000, seed: int = 1) -> dict[str, np.ndarray]:
    """Cost per barrel of the refiner's cargo, unhedged and hedged, on simulated paths.
    Physical assessment = futures + basis; both are random walks from today (day 0)."""
    rng = np.random.default_rng(seed)
    days = pricing_days(BL_DAY, 2, 2)
    horizon = max(days) + 1
    f = F0 + np.cumsum(rng.normal(0.0, SIGMA_F, (n_paths, horizon)), axis=1)
    b = B0 + np.cumsum(rng.normal(0.0, SIGMA_B, (n_paths, horizon)), axis=1)
    physical = (f + b)[:, days].mean(axis=1) + DIFF          # the formula price
    hedge_gain = (f[:, days] - F0).mean(axis=1)              # bought 700 lots today, sold 140 a day
    return {"unhedged": physical, "hedged": physical - hedge_gain}


def hedged_sd_theory() -> float:
    """Standard deviation of the hedged cost: that of the average basis over the pricing days."""
    days = np.array(pricing_days(BL_DAY, 2, 2)) + 1          # steps taken by day d (day 0 is one step)
    cov = SIGMA_B ** 2 * np.minimum.outer(days, days)
    return float(np.sqrt(cov.sum()) / len(days))


def back_to_back() -> dict[str, object]:
    """The weekend problem's trading house: buys FOB priced 2-1-2 around loading (day 10) at
    Dated + 0.20, sells CIF priced 2-1-2 around discharge (day 30) at Dated + 1.10."""
    buy = Leg(+1, VOLUME, tuple(pricing_days(10, 2, 2)), 0.20)
    sell = Leg(-1, VOLUME, tuple(pricing_days(30, 2, 2)), 1.10)
    prof = [(d, exposure([buy, sell], d)) for d in range(0, 36)]
    margin = locked_margin(buy, sell, freight=0.65, insurance=0.03)
    return {"buy": buy, "sell": sell, "profile": prof, "trades": hedge_trades([buy, sell]),
            "margin": margin, "margin_usd": margin * VOLUME,
            "days_full": sum(1 for _, e in prof if e == VOLUME)}


def unhedged_sd_usd(days_apart: int = 20, sigma: float = SIGMA_F) -> float:
    """Standard deviation of the unhedged P&L of a cargo whose purchase and sale price `days_apart`
    business days apart: the benchmark's move over that gap, times the volume."""
    return sigma * np.sqrt(days_apart) * VOLUME


def load_differential() -> list[tuple[str, float, float]]:
    """(month, WTI, Brent) monthly averages of daily spot prices, $/bbl."""
    with open(DATA / "wti_brent_monthly.csv") as fh:
        return [(r["month"], float(r["wti"]), float(r["brent"])) for r in csv.DictReader(fh)]


def differential_stats() -> dict[str, object]:
    rows = load_differential()
    spread = [(m, w - b) for m, w, b in rows]
    lo = min(spread, key=lambda x: x[1])
    return {"n": len(rows), "mean": float(np.mean([s for _, s in spread])), "min": lo,
            "above": sum(1 for _, s in spread if s > 0),
            "since2011_above": sum(1 for m, s in spread if m >= "2011-01" and s > 0),
            "last": spread[-1]}
