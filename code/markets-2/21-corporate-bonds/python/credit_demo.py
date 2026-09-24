"""Chapter 21 of Book 2: corporate bonds. The spread measures of one seven-year corporate bond, its
option-adjusted spread if callable, the spread of high-quality corporate yields over Treasuries since
1984, and the price path of a fallen angel. Curves, the bond and the downgrade are illustrative; the
spread history is from US Treasury and Federal Reserve data."""
import csv
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/spreads"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/normalvol"))
from firm_normalvol import bachelier
from firm_spreads import (
    asset_swap_spread,
    g_spread,
    i_spread,
    interp,
    spread_price_impact,
    yield_from_price,
    z_spread,
)

DATA = pathlib.Path(__file__).resolve().parents[4] / "data/markets-2"
GOVT = [(2, 0.0420), (5, 0.0435), (7, 0.0450), (10, 0.0468), (30, 0.0510)]
SWAP = [(2, 0.0410), (5, 0.0415), (7, 0.0425), (10, 0.0440), (30, 0.0460)]
ZERO = [(t, 2 * math.log(1 + r / 2)) for t, r in SWAP]          # swap par rates used as zero rates
COUPON, YEARS, PRICE = 5.50, 7, 99.00


def measures() -> dict[str, float]:
    y = yield_from_price(COUPON, YEARS, PRICE)
    return {"yield": y, "g": g_spread(y, YEARS, GOVT), "i": i_spread(y, YEARS, SWAP),
            "z": z_spread(COUPON, YEARS, PRICE, ZERO), "asw": asset_swap_spread(COUPON, YEARS, PRICE, ZERO),
            "govt7": interp(GOVT, YEARS), "swap7": interp(SWAP, YEARS)}


def callable_oas(vol: float = 0.0100, call_year: int = 3) -> dict[str, float]:
    """The same bond callable at par in three years: the issuer's call is a receiver swaption on the
    remaining four years struck at the coupon; its cost, as a running spread, is subtracted."""
    fwd = interp(SWAP, YEARS)                                   # flat-ish forward, illustrative
    dates = [call_year + k / 2 for k in range(1, 2 * (YEARS - call_year) + 1)]
    ann = sum(math.exp(-interp(ZERO, t) * t) / 2 for t in dates)
    option = bachelier(fwd, COUPON / 100, call_year, vol, ann, payer=False) * 100      # per 100 face
    full_ann = sum(math.exp(-interp(ZERO, k / 2) * k / 2) / 2 for k in range(1, 2 * YEARS + 1))
    z = measures()["z"]
    return {"option": option, "cost_bp": option / (100 * full_ann) * 1e4, "oas": z - option / (100 * full_ann)}


def load_hqm() -> list[tuple[str, float, float]]:
    with open(DATA / "hqm_gs10_monthly.csv") as f:
        return [(r["date"], float(r["hqm10"]), float(r["gs10"])) for r in csv.DictReader(f)]


# ---- the fallen angel ---------------------------------------------------------------------------
DURATION, FACE = 6.0, 50e6
PATH = [(-6, 2.50), (-3, 2.90), (-1, 3.30), (0, 4.00), (1, 3.80), (3, 3.50), (6, 3.45)]     # months, spread %


def fallen_angel() -> dict[str, float]:
    s = dict(PATH)
    fair = 3.50
    return {"pre_to_down": spread_price_impact(DURATION, (s[0] - s[-6]) / 100),
            "overshoot_pts": spread_price_impact(DURATION, (s[0] - fair) / 100),
            "overshoot_usd": spread_price_impact(DURATION, (s[0] - fair) / 100) / 100 * FACE,
            "buyer_gain_pts": -spread_price_impact(DURATION, (s[0] - s[3]) / 100),
            "reaction_at_down": spread_price_impact(DURATION, (s[0] - s[-1]) / 100)}

