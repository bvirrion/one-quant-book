"""Net cost per share across venues under tiered fees (Chapter 29).
The maker-taker schedule is one exchange's published schedule (see the chapter's ledger); the
inverted and flat venues, and the clearing and regulatory costs, are illustrative."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/feesched"))
from firm_feesched import Schedule, Tier, all_in_per_share

TCV = 12e9                          # an assumed total consolidated volume, shares a day

MAKER_TAKER = Schedule("maker-taker exchange", -0.0016, 0.0030, (
    Tier("1", 0.0006, -0.0020), Tier("2", 0.0020, -0.0023), Tier("3", 0.0025, -0.0028), Tier("7", 0.0100, -0.0031)))
INVERTED = Schedule("inverted exchange", 0.0010, -0.0006)      # illustrative: makers pay, takers are paid
FLAT = Schedule("flat-fee venue", 0.0003, 0.0003)               # illustrative

VENUES = (MAKER_TAKER, INVERTED, FLAT)
CLEARING, REGULATORY = 0.0002, 0.0001                           # per share, illustrative


def cost_table(adav: float) -> list[tuple[str, float, float]]:
    """(venue, all-in cost of a passive share, all-in cost of an aggressive share), in dollars."""
    return [(s.venue, all_in_per_share(s, adav, TCV, True, CLEARING, REGULATORY).total,
             all_in_per_share(s, adav, TCV, False, CLEARING, REGULATORY).total) for s in VENUES]


def monthly_rebate(adav: float, days: int = 21) -> float:
    return -MAKER_TAKER.daily_bill(adav, 0.0, TCV) * days
