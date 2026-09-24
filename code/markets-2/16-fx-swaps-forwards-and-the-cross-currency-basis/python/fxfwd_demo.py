"""Chapter 16 of Book 2: FX swaps, forwards and the cross-currency basis. USDJPY forward points from
two money-market rates, the basis they imply, a yen investor's hedged Treasury yield since 2018,
and the Federal Reserve's swap lines. Rates are overnight rates used as proxies for term rates; the
basis levels are illustrative."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/fxfwd"))
from firm_fxfwd import basis_on_quote, forward, fx_swap_legs, hedged_yield, points

DATA = pathlib.Path(__file__).resolve().parents[4] / "data/markets-2"
SPOT = 156.87            # USDJPY, Federal Reserve H.10, 18 September 2026
R_USD = 0.0368           # SOFR, 31 August 2026
R_JPY = 0.00977          # Japanese call-money rate, August 2026 average
UST10, JGB10 = 0.0475, 0.0294   # 31 August 2026 (Treasury), August 2026 average (JGB)
BASIS = -0.0025          # illustrative three-month basis on the yen leg
TENORS = [("1W", 7), ("1M", 30), ("2M", 61), ("3M", 91), ("6M", 182), ("9M", 273), ("1Y", 365)]


def usdjpy_forward(days: int, basis: float = 0.0) -> float:
    return forward(SPOT, R_JPY, R_USD, days, basis_quote=basis, dc_quote=365, dc_base=360)


def points_curve() -> list[tuple[str, int, float, float]]:
    """(tenor, days, points without basis, points with the illustrative basis), in pips of 0.01 yen."""
    return [(t, d, points(usdjpy_forward(d), SPOT, 0.01), points(usdjpy_forward(d, BASIS), SPOT, 0.01))
            for t, d in TENORS]


def three_month() -> dict[str, float]:
    f0, f = usdjpy_forward(91), usdjpy_forward(91, BASIS)
    return {"fwd0": f0, "fwd": f, "pts0": points(f0, SPOT, 0.01), "pts": points(f, SPOT, 0.01),
            "basis_back": basis_on_quote(SPOT, f, R_JPY, R_USD, 91, dc_quote=365),
            "tn_pts": points(usdjpy_forward(1), SPOT, 0.01), "legs": fx_swap_legs(10e6, SPOT, f)}


def hedged_now() -> dict[float, float]:
    return {b: hedged_yield(UST10, R_USD, R_JPY, b) for b in (0.0, -0.0025, -0.0050)}


def load_hedged() -> list[tuple[str, float, float, float, float]]:
    with open(DATA / "hedged_ust_jpy.csv") as f:
        return [(r["date"], float(r["ust10"]), float(r["sofr"]), float(r["jp_call"]), float(r["jgb10"]))
                for r in csv.DictReader(f)]


def hedged_series() -> list[tuple[str, float, float, float]]:
    """(date, unhedged UST %, UST hedged with zero basis %, JGB %)."""
    return [(d, u, 100 * hedged_yield(u / 100, s / 100, j / 100, 0.0), g) for d, u, s, j, g in load_hedged()]


def load_swaplines() -> list[tuple[str, float]]:
    with open(DATA / "fed_swaplines_monthly.csv") as f:
        return [(r["date"], float(r["usd_bn"])) for r in csv.DictReader(f)]
