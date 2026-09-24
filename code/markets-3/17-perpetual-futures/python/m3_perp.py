"""Book 3, Chapter 17: the funding formula on a synthetic premium series, the inverse contract's P&L in
coin, and the funding (cash-and-carry) trade on a perpetual."""
import csv
import math
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/perp"))
from firm_perp import average_premium, funding_rate, pnl_inverse  # noqa: E402

SAMPLES = 5_760                                     # one every 5 seconds over 8 hours


def premium_path(level: float, seed: int, phi: float = 0.999, sd: float = 0.0002) -> list[float]:
    """Premium index samples over one interval: AR(1) around `level`."""
    rng = random.Random(seed)
    p, out = level, []
    for _ in range(SAMPLES):
        p = level + phi * (p - level) + rng.gauss(0, sd * math.sqrt(1 - phi * phi))
        out.append(p)
    return out


def month_of_funding(levels: list[float], seed: int = 17) -> list[tuple[int, float, float]]:
    """(interval, time-weighted premium, funding rate) for a sequence of premium levels."""
    out = []
    for i, lv in enumerate(levels):
        p = average_premium(premium_path(lv, seed + i))
        out.append((i, p, funding_rate(p)))
    return out


def regimes() -> list[float]:
    """Thirty days of three intervals: calm, a rally with a rich perpetual, a sell-off, calm."""
    return [0.0001] * 30 + [0.0012] * 21 + [-0.0008] * 12 + [0.0002] * 27


def inverse_curve(entry: float = 60_000.0, contracts: float = 60_000.0):
    """P&L in BTC of a long inverse position and its tangent at entry, for prices 30,000 to 120,000."""
    rows = []
    for s in range(30_000, 120_001, 2_500):
        rows.append((s, pnl_inverse(contracts, entry, s), contracts / entry**2 * (s - entry)))
    return rows


def margin_to_survive(rally: float = 0.30, maintenance: float = 0.005) -> float:
    """Margin, as a share of the initial notional, a short perpetual needs to survive a rally."""
    return rally + maintenance * (1 + rally)


def funding_trade(funding_annual: float, spot_fee: float = 0.001, perp_fee: float = 0.0005,
                  margin: float | None = None) -> float:
    """Annual return on capital of long spot + short perpetual held a year at a constant price: funding
    received less entry and exit fees, over the spot outlay plus the short's margin."""
    m = margin_to_survive() if margin is None else margin
    return (funding_annual - 2 * (spot_fee + perp_fee)) / (1 + m)


def yearly_funding(path: str | None = None) -> dict[int, float]:
    path = path or str(ROOT / "data/markets-3/binance_btcusdt_funding_by_year.csv")
    return {int(r["year"]): float(r["mean_annualised_pct"]) / 100 for r in csv.DictReader(open(path))}
