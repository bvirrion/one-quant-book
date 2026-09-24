"""Chapter 8 of Book 2: short-term interest-rate futures. Illustrative one-month overnight-rate
futures around the FOMC meetings of 28 October and 9 December 2026 and 27 January 2027 (the
meeting dates are the Federal Reserve's; the prices are illustrative), the implied policy path,
the effect of a year-end turn, IMM dates, and the convexity adjustment."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/meetings"))
from firm_meetings import MonthContract, convexity_adjustment, move_probability, policy_path, rate_after, strip_rate

START_RATE = 3.87          # overnight rate after the September 2026 hike (illustrative level)
OCT = MonthContract(2026, 10, 96.1275, dt.date(2026, 10, 28))
NOV = MonthContract(2026, 11, 96.1025)
DEC = MonthContract(2026, 12, 96.0400, dt.date(2026, 12, 9))
JAN = MonthContract(2027, 1, 95.9900, dt.date(2027, 1, 27))


def path() -> list[tuple[str, float]]:
    return policy_path([OCT, NOV, DEC, JAN], START_RATE)


def december(turn_bp: float) -> dict[str, float]:
    """The December meeting with a year-end turn of turn_bp on the 31 December fixing."""
    rate_in = rate_after(NOV, 0.0)
    c = MonthContract(2026, 12, DEC.price, DEC.meeting, turn_days=1 if turn_bp else 0, turn_bp=turn_bp)
    r = rate_after(c, rate_in)
    return {"rate_in": rate_in, "rate_after": r, "probability": move_probability(r, rate_in)}


def turn_sensitivity() -> list[tuple[float, float]]:
    return [(t, 100 * december(t)["probability"]) for t in range(0, 41, 2)]


def imm_date(year: int, month: int) -> dt.date:
    """Third Wednesday of the month."""
    d = dt.date(year, month, 1)
    first_wed = d + dt.timedelta(days=(2 - d.weekday()) % 7)
    return first_wed + dt.timedelta(days=14)


def reference_quarters(year: int) -> list[tuple[dt.date, dt.date]]:
    """Three-month contract reference quarters ending in each quarterly month of `year`."""
    out = []
    for m in (3, 6, 9, 12):
        end = imm_date(year, m)
        py, pm = (year, m - 3) if m > 3 else (year - 1, 12)
        out.append((imm_date(py, pm), end))
    return out


def convexity_table() -> list[tuple[float, float, float, float]]:
    """(start in years, adjustment in bp for sigma 0.8%, 1.0%, 1.2%) for a three-month rate."""
    out = []
    for k in range(0, 41):
        t1 = k * 0.25
        out.append((t1, *(1e4 * convexity_adjustment(s, t1, t1 + 0.25) for s in (0.008, 0.010, 0.012))))
    return out


__all__ = ["strip_rate"]
