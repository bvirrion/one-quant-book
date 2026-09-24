"""Chapter 1 of Book 2: the short rate. An illustrative month of overnight fixings around a
25 bp hike, a stylised demand curve for reserves inside a corridor, and the Federal Reserve's
balance sheet of 16 September 2026 (H.4.1, source ledger F7)."""
import datetime as dt
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/rfr"))
from firm_rfr import Calendar, Convention, compound_in_arrears, simple_average

# US calendar for the example month: 7 September 2026 is Labor Day (first Monday of September).
CAL = Calendar(frozenset({dt.date(2026, 9, 7)}))
START, END = dt.date(2026, 9, 1), dt.date(2026, 10, 1)
HIKE = dt.date(2026, 9, 17)          # first fixing at the new administered rates
QUARTER_END = dt.date(2026, 9, 30)

# Illustrative fixings (not published rates): 3.62% before the hike, 3.87% after, 3.95% at quarter-end.
BEFORE, AFTER, QEND = 0.0362, 0.0387, 0.0395


def fixings() -> dict[dt.date, float]:
    out, d = {}, dt.date(2026, 8, 17)
    while d < dt.date(2026, 10, 10):
        if CAL.is_business_day(d):
            out[d] = QEND if d == QUARTER_END else (AFTER if d >= HIKE else BEFORE)
        d += dt.timedelta(days=1)
    return out


def month_summary() -> dict[str, float]:
    fx = fixings()
    return {
        "simple": simple_average(fx, CAL, START, END),
        "compounded": compound_in_arrears(fx, CAL, START, END),
        "lookback5": compound_in_arrears(fx, CAL, START, END, Convention(lookback=5)),
        "shift5": compound_in_arrears(fx, CAL, START, END, Convention(lookback=5, shift=True)),
        "lockout2": compound_in_arrears(fx, CAL, START, END, Convention(lockout=2)),
    }


def running_compounded() -> list[tuple[dt.date, float, float]]:
    """(day, fixing, compounded rate from START to the next business day) for the chart."""
    fx = fixings()
    days = CAL.business_days(START, END)
    out = []
    for i, d in enumerate(days):
        nxt = days[i + 1] if i + 1 < len(days) else END
        out.append((d, fx[d], compound_in_arrears(fx, CAL, START, nxt)))
    return out


# ---- a corridor: overnight rate as a function of the supply of reserves ---------------------------

def overnight_rate(reserves: float, deposit: float, lending: float, satiation: float = 3.0,
                   steepness: float = 2.5) -> float:
    """Stylised demand for reserves: banks pay up to the lending rate when reserves are scarce and
    no less than the deposit rate when they are abundant (a logistic between the two)."""
    return deposit + (lending - deposit) / (1.0 + math.exp(steepness * (reserves - satiation)))


# ---- the Fed's balance sheet, Wednesday 16 September 2026, USD billion (H.4.1) --------------------
FED_TOTAL_ASSETS = 6746.548
FED_TREASURIES = 4554.450
FED_MBS = 1913.523
FED_RESERVES = 3013.794
FED_TGA = 877.028
FED_RRP = 323.803


def fed_balance_sheet() -> dict[str, dict[str, float]]:
    other_assets = FED_TOTAL_ASSETS - FED_TREASURIES - FED_MBS
    rest = FED_TOTAL_ASSETS - FED_RESERVES - FED_TGA - FED_RRP
    return {
        "assets": {"Treasuries": FED_TREASURIES, "MBS": FED_MBS, "other": other_assets},
        "liabilities": {"reserves": FED_RESERVES, "TGA": FED_TGA, "reverse repo": FED_RRP,
                        "currency and other": rest},
    }


# ---- the weekend problem: a corridor, two banks, thirty days --------------------------------------

def facility_interest(amount: float, rate: float, days: int, basis: int = 360) -> float:
    return amount * rate * days / basis


def problem_numbers() -> dict[str, float]:
    """Bank A holds 2 billion of excess reserves, bank B is 2 billion short, for 30 days.
    Corridor 2.25 / 2.65 for 15 days, then 2.50 / 2.90 (moved up 25 bp) for 15 days."""
    amt = 2_000_000_000.0
    p1 = (0.0225, 0.0265)
    p2 = (0.0250, 0.0290)
    a_dep = facility_interest(amt, p1[0], 15) + facility_interest(amt, p2[0], 15)
    b_lend = facility_interest(amt, p1[1], 15) + facility_interest(amt, p2[1], 15)
    mid1, mid2 = sum(p1) / 2, sum(p2) / 2
    interbank = facility_interest(amt, mid1, 15) + facility_interest(amt, mid2, 15)
    return {
        "a_deposit": a_dep, "b_lending": b_lend, "gap": b_lend - a_dep,
        "interbank": interbank, "a_gain": interbank - a_dep, "b_saving": b_lend - interbank,
    }
