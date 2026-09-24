"""Book 3, Chapter 29: the sizes of markets on one scale, turnover velocity, the fixed moments of the
trading day in UTC, and the shifts a round-the-clock desk needs."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/marketmap"))
from firm_marketmap import Market, every_day, plan_shifts, staffed_minutes  # noqa: E402, F401

# Daily turnover, USD billion, with the measure each source uses (see the chapter's ledger).
SIZES = [("FX, all instruments (April 2025)", 9_600.0), ("US fixed income (2026 to August)", 1_659.2),
         ("US Treasuries (2026 to August)", 1_203.6), ("BTC perpetual, one venue (24 h)", 17.65),
         ("BTC spot, one venue (24 h)", 1.90), ("BTC perpetual, another venue (24 h)", 1.58)]

# Fixed moments of a (northern-summer) weekday in UTC minutes: (label, start, end).
MOMENTS = [("perpetual funding", 0, 0), ("perpetual funding", 480, 480), ("perpetual funding", 960, 960),
           ("crypto options expiry", 480, 480), ("EU day-ahead auction", 600, 600),
           ("LME official prices published", 680, 745), ("US equities core session", 810, 1200),
           ("bitcoin reference rate window", 1140, 1200)]


def turnover_velocity(daily_turnover: float, outstanding: float) -> float:
    """Share of the amount outstanding that trades each day."""
    return daily_turnover / outstanding


def desks() -> list[Market]:
    """The firm's staffing choices (illustrative): crypto around the clock, a European power desk 05:00-17:00
    UTC, a US desk 12:00-21:00 UTC on weekdays."""
    wk = range(5)
    return [Market("crypto", None, "centralised and decentralised venues", False, every_day(0, 1440)),
            Market("European power", None, "exchanges and brokers", True, every_day(300, 1020, wk)),
            Market("US rates and equities", None, "exchanges and dealers", True, every_day(720, 1260, wk))]


def shifts(length_h: float = 9, overlap_h: float = 1, weekday: int = 2) -> list[tuple]:
    return plan_shifts(desks(), weekday, length_h, overlap_h)
