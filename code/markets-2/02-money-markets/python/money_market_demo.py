"""Chapter 2 of Book 2: money markets. An illustrative bill curve in three quoting conventions, a
quarter-end turn in overnight and one-week rates, and the numbers of the year-end problem."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/mmyield"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/rfr"))
from firm_mmyield import implied_turn, investment_rate, money_market_yield, price_from_discount, year_days
from firm_rfr import Calendar, compound_in_arrears

# ---- an illustrative bill curve (discount rates, not market quotes) -------------------------------
ISSUE = dt.date(2026, 9, 24)
WEEKS = [4, 6, 8, 13, 17, 26, 52]
DISCOUNT = [0.0386, 0.0385, 0.0384, 0.0382, 0.0380, 0.0376, 0.0370]


def bill_curve() -> list[dict[str, float]]:
    y = year_days(ISSUE)
    rows = []
    for w, d in zip(WEEKS, DISCOUNT, strict=True):
        days = 7 * w
        p = price_from_discount(d, days)
        rows.append({"weeks": w, "days": days, "discount": d, "price": p,
                     "mmy": money_market_yield(p, days), "bey": investment_rate(p, days, y)})
    return rows


# ---- a quarter-end turn: overnight fixings and one-week term rates by start date ------------------
CAL = Calendar(frozenset({dt.date(2026, 10, 12)}))     # Columbus Day, no SOFR fixing
QUARTER_END = dt.date(2026, 9, 30)
NORMAL, TURN = 0.0387, 0.0395


def overnight() -> dict[dt.date, float]:
    out, d = {}, dt.date(2026, 9, 14)
    while d < dt.date(2026, 10, 31):
        if CAL.is_business_day(d):
            out[d] = TURN if d == QUARTER_END else NORMAL
        d += dt.timedelta(days=1)
    return out


def one_week_by_start() -> list[tuple[dt.date, float]]:
    """Rate of a one-week deposit starting each business day, if it earned the overnight path."""
    fx = overnight()
    out = []
    for d in CAL.business_days(dt.date(2026, 9, 17), dt.date(2026, 10, 9)):
        out.append((d, compound_in_arrears(fx, CAL, d, d + dt.timedelta(days=7))))
    return out


# ---- the weekend problem: USD 500 million over year-end 2026 --------------------------------------
AMOUNT = 500_000_000.0
TERM_1W = 0.0395           # quoted one-week deposit, Monday 28 December 2026 to Monday 4 January 2027
NORMAL_ON = 0.0388         # assumed overnight rate on the three ordinary nights
ON_RRP = 0.0375            # the Fed's reverse repo offering rate (Chapter 1, Box 1.1)


def problem_numbers() -> dict[str, float]:
    turn = implied_turn(TERM_1W, 7, NORMAL_ON, 3, 4)
    deposit = AMOUNT * TERM_1W * 7 / 360
    rrp = AMOUNT * ((1 + ON_RRP / 360) ** 3 * (1 + ON_RRP * 4 / 360) - 1)
    two_week = ((1 + NORMAL_ON / 360) ** 10 * (1 + turn * 4 / 360) - 1) * 360 / 14
    return {
        "turn": turn,
        "premium_bp": (turn - NORMAL_ON) * 1e4,
        "deposit": deposit,
        "deposit_bey": TERM_1W * 365 / 360,
        "rrp": rrp,
        "extra_cost": AMOUNT * (turn - NORMAL_ON) * 4 / 360,
        "rrp_shortfall": AMOUNT * (turn - ON_RRP) * 4 / 360,
        "two_week": two_week,
    }
