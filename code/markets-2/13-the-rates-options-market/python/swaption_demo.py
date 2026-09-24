"""Chapter 13 of Book 2: the rates options market. Normal against lognormal quotes, a slice of an
illustrative volatility cube, a swaption straddle, a cap, and the callable bond a bank swaps for an
issuer. The curve is flat at 4% (annual compounding); volatilities are illustrative."""
import csv
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/normalvol"))
from firm_normalvol import atm_straddle, bachelier, bp_per_day, normal_to_black, normal_vega

DATA = pathlib.Path(__file__).resolve().parents[4] / "data/markets-2"
RATE = 0.04


def annuity(start: int, end: int, rate: float = RATE) -> float:
    """Annual fixed-leg annuity of a swap from year `start` to year `end`, per unit notional."""
    return sum((1 + rate) ** -k for k in range(start + 1, end + 1))


# ---- normal against lognormal ------------------------------------------------------------------
VOL_N = 0.0090            # 90 bp a year


def black_equivalents() -> list[tuple[float, float]]:
    """(forward %, Black vol %) matching an at-the-money one-year option at 90 bp normal."""
    grid = [0.38, 0.4, 0.45, 0.5, 0.6, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0]
    return [(f, 100 * normal_to_black(f / 100, f / 100, 1.0, VOL_N)) for f in grid]


def no_black_below(t: float = 1.0, vol: float = VOL_N) -> float:
    """Forward below which no Black volatility matches an at-the-money normal price."""
    return vol * math.sqrt(t) / math.sqrt(2 * math.pi)


def load_negative_yields() -> list[tuple[str, float, float]]:
    with open(DATA / "oecd_10y_monthly.csv") as f:
        return [(r["date"], float(r["DE"]), float(r["JP"])) for r in csv.DictReader(f)]


# ---- an illustrative cube slice and smile --------------------------------------------------------
EXPIRIES = [0.25, 0.5, 1, 2, 5, 10]
ATM = {2: [110, 112, 110, 105, 95, 85], 10: [95, 96, 95, 93, 88, 80], 30: [85, 86, 86, 85, 82, 76]}   # bp


def smile(offset_pct: float) -> float:
    """Illustrative 1y x 10y normal vol (bp) against strike minus forward (percentage points)."""
    return 95.0 - 1.5 * offset_pct + 3.0 * offset_pct ** 2


def straddle_1y10y(notional: float = 100e6) -> dict[str, float]:
    a = annuity(1, 11)
    vol = ATM[10][2] / 1e4
    prem = atm_straddle(1.0, vol, a) * notional
    return {"annuity": a, "vol": vol, "premium": prem, "premium_bp": prem / notional * 1e4,
            "breakeven_bp": prem / notional / a * 1e4, "bp_day": bp_per_day(vol)}


def cap(notional: float = 100e6, strike: float = 0.045, vol: float = 0.0100, years: int = 5) -> dict[str, float]:
    """Annual caplets on the 12-month rate, fixing at 1..years-1 and paid a year later."""
    caplets = [notional * bachelier(RATE, strike, t, vol, (1 + RATE) ** -(t + 1)) for t in range(1, years)]
    floors = [notional * bachelier(RATE, 0.035, t, vol, (1 + RATE) ** -(t + 1), payer=False) for t in range(1, years)]
    return {"caplets": caplets, "cap": sum(caplets), "floor": sum(floors), "collar": sum(caplets) - sum(floors)}


# ---- the callable issuer ------------------------------------------------------------------------
ISSUE = 500e6
COUPON = 0.045            # 10-year bond, callable at par once, in 3 years
VOL_3Y7Y = 0.0100


def callable_swap() -> dict[str, float]:
    """The dealer's cancellation right is a 3y x 7y receiver swaption struck at the coupon."""
    a = annuity(3, 10)
    rec = bachelier(RATE, COUPON, 3.0, VOL_3Y7Y, a, payer=False) * ISSUE
    vega = normal_vega(RATE, COUPON, 3.0, VOL_3Y7Y, a) * ISSUE * 1e-4
    h = 1e-6
    up, dn = (bachelier(RATE + x, COUPON, 3.0, VOL_3Y7Y, a, payer=False) for x in (h, -h))
    delta = (up - dn) / (2 * h) * ISSUE * 1e-4
    straddle_vega = 2 * normal_vega(RATE, RATE, 3.0, VOL_3Y7Y, a) * 1e-4           # per unit notional
    return {"annuity": a, "price": rec, "price_bp": rec / ISSUE * 1e4, "vega": vega, "delta": delta,
            "straddle_vega_100m": straddle_vega * 100e6, "straddles": vega / straddle_vega,
            "running_bp": rec / (ISSUE * annuity(0, 10)) * 1e4, "vol_down_2": -2 * vega,
            "forward_move_needed": COUPON - RATE}
