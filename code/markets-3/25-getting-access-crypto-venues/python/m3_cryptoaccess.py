"""Book 3, Chapter 25: a month's fees on five venues, spreading against concentrating, a tier match, and the
uptime a quoting strategy achieves against a programme's spread and depth requirements."""
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/mmprogram"))
from firm_mmprogram import Snapshot, VolTier, monthly_fees, rebate, tier_for, uptime  # noqa: E402

# Two published spot schedules (dated box of the chapter) and three illustrative ones.
BINANCE = [VolTier(0, 10, 10), VolTier(1e6, 9, 10), VolTier(5e6, 8, 10), VolTier(20e6, 4, 6), VolTier(75e6, 4, 5.2),
           VolTier(150e6, 2.5, 3.1), VolTier(400e6, 2.0, 2.9), VolTier(800e6, 1.9, 2.8), VolTier(2e9, 1.6, 2.5),
           VolTier(4e9, 1.1, 2.3)]
KRAKEN = [VolTier(0, 40, 80), VolTier(2.5e3, 30, 60), VolTier(1e4, 22, 38), VolTier(2.5e4, 20, 35),
          VolTier(5e4, 15, 30), VolTier(1e5, 12, 25), VolTier(2.5e5, 10, 22), VolTier(5e5, 8, 20),
          VolTier(1e6, 6, 18), VolTier(2.5e6, 4, 15), VolTier(5e6, 2, 12), VolTier(1e7, 0, 10), VolTier(5e7, 0, 9),
          VolTier(1e8, 0, 8), VolTier(2.5e8, 0, 7), VolTier(4e8, 0, 6), VolTier(5e8, 0, 5)]
VENUE_C = [VolTier(0, 10, 10), VolTier(1e7, 5, 7), VolTier(1e8, 3, 5), VolTier(5e8, 1, 3)]
VENUE_D = [VolTier(0, 15, 20), VolTier(5e7, 6, 10), VolTier(2.5e8, 2, 5)]
VENUE_E = [VolTier(0, 20, 25), VolTier(1e8, 8, 12), VolTier(5e8, 3, 6)]
VENUES = {"Binance": BINANCE, "Kraken": KRAKEN, "C": VENUE_C, "D": VENUE_D, "E": VENUE_E}

MONTH, MAKER = 600e6, 0.7


def plan_fees(split: dict[str, float], maker: float = MAKER) -> dict[str, float]:
    return {v: monthly_fees(vol, maker, VENUES[v]) for v, vol in split.items()}


def spread_vs_concentrate() -> tuple[dict, dict]:
    spread = plan_fees({v: MONTH / 5 for v in VENUES})
    conc = plan_fees({"Binance": MONTH / 2, "Kraken": MONTH / 2})
    return spread, conc


def tier_match_value(volume: float = MONTH / 5) -> float:
    """What venue C's fees fall by if it matches the firm's Binance tier on its full month there."""
    matched = tier_for(MONTH / 2, BINANCE)
    return monthly_fees(volume, MAKER, VENUE_C) - monthly_fees(volume, MAKER, VENUE_C, matched=matched)


def quoting_snapshots(n: int = 20_000, seed: int = 25, base_spread_bp: float = 8.0,
                      thin_at: float = 2.0) -> list[Snapshot]:
    """A strategy that quotes USD 60,000 a side at a spread that widens with volatility and that pulls its
    quotes above three times normal volatility and halves its depth above `thin_at` times, sampled once a minute."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        vol = rng.lognormvariate(0.0, 0.6)                 # volatility relative to normal
        spread = base_spread_bp * vol
        if vol > 3.0:
            out.append(Snapshot(100.0, None, None, 0.0, 0.0))
            continue
        depth = 60_000 if vol < thin_at else 30_000
        out.append(Snapshot(100.0, 100.0 * (1 - spread / 2e4), 100.0 * (1 + spread / 2e4), depth, depth))
    return out


def uptime_curve() -> list[tuple[float, float]]:
    snaps = quoting_snapshots()
    return [(s, uptime(snaps, s, 50_000)) for s in range(4, 41, 2)]


def programme_value(maker_volume: float = MONTH / 2 * MAKER, rebate_bp: float = 0.5, required: float = 0.9,
                    max_spread_bp: float = 20.0, thin_at: float = 2.0) -> tuple[float, float]:
    u = uptime(quoting_snapshots(thin_at=thin_at), max_spread_bp, 50_000)
    return u, rebate(maker_volume, rebate_bp, u, required)


def effective_fee_curve(maker: float = MAKER) -> list[tuple[float, float, float]]:
    """(monthly volume USD million, Binance bp, Kraken bp) for the blended maker-taker fee of each schedule."""
    out = []
    for k in range(0, 41):
        vol = 10 ** (5 + k * 0.1)                        # 0.1 to 1,000 USD million, log-spaced
        b, kr = tier_for(vol, BINANCE), tier_for(vol, KRAKEN)
        out.append((vol / 1e6, maker * b.maker_bp + (1 - maker) * b.taker_bp,
                    maker * kr.maker_bp + (1 - maker) * kr.taker_bp))
    return out
