"""Chapter 4 of Book 2: the Treasury market. A synthetic ten-year auction (seeded bid book around
a when-issued yield), the dealer of the weekend problem, and the 2020 Treasury purchases of the
Federal Reserve (FRED series TREAST, data/markets-2/treast_2020.csv)."""
import csv
import datetime as dt
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/tsyauction"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/bond"))
from firm_bond import Bond
from firm_tsyauction import Bid, cumulative_demand, run_auction, tail_bp

OFFERING = 42_000.0          # USD million
NONCOMP = 300.0
WI = 0.04180                 # when-issued yield at the bid deadline, 13:00
N_DEALERS = 26
DEALER = "D07"               # the dealer of the weekend problem
DEALER_BIDS = [(0.04188, 500.0), (0.04195, 500.0), (0.04205, 615.0)]


def bid_book(seed: int = 4) -> list[Bid]:
    """Indirect and direct bidders cluster around the when-issued level; each primary dealer bids
    its pro-rata share, laddered above it. Yields in thousandths of a percent."""
    rng = np.random.default_rng(seed)
    bids = []
    for i in range(40):                                    # indirect bidders (through dealers)
        y = round(WI + rng.normal(0.0001, 0.00008), 5)
        bids.append(Bid(f"I{i:02d}", y, float(rng.integers(3, 12) * 100)))
    for i in range(15):                                    # direct bidders
        y = round(WI + rng.normal(0.00012, 0.00008), 5)
        bids.append(Bid(f"X{i:02d}", y, float(rng.integers(2, 8) * 100)))
    share = OFFERING / N_DEALERS
    for i in range(N_DEALERS):                             # primary dealers, pro rata, laddered
        name = f"D{i:02d}"
        if name == DEALER:
            bids += [Bid(name, y, a) for y, a in DEALER_BIDS]
            continue
        base = round(WI + rng.normal(0.00012, 0.00005), 5)
        bids += [Bid(name, base, share * 0.3), Bid(name, round(base + 0.00008, 5), share * 0.3),
                 Bid(name, round(base + 0.00020, 5), share * 0.4)]
    return bids


def auction():
    return run_auction(OFFERING, NONCOMP, bid_book())


def summary() -> dict[str, float]:
    r = auction()
    groups = {"indirect": "I", "direct": "X", "dealers": "D"}
    shares = {g: sum(v for k, v in r.awards.items() if k.startswith(p)) / (OFFERING - NONCOMP)
              for g, p in groups.items()}
    return {"stop": r.stop, "tail_bp": tail_bp(r.stop, WI), "btc": r.bid_to_cover,
            "allot": r.allotment_at_stop, "tendered": r.competitive_tendered, **shares,
            "dealer_award": r.awards.get(DEALER, 0.0)}


def demand_curve() -> list[tuple[float, float]]:
    return cumulative_demand(bid_book(), OFFERING)


# ---- the dealer's P&L: awarded bonds against a when-issued short at 13:00 ------------------------
NOTE = Bond(4.125, dt.date(2036, 11, 15))    # the new ten-year, coupon set after the auction
ISSUE = dt.date(2026, 11, 16)


def dv01_per_million(y: float) -> float:
    return NOTE.risk(y, ISSUE)["dv01"] * 1e4


def dealer_pnl(award: float, stop: float, hedge_yield: float, cost_bp: float = 0.25) -> float:
    """USD P&L of buying `award` (USD million) at the stop-out while short the same amount of
    when-issued sold at hedge_yield, less a round-trip cost of cost_bp basis points of DV01."""
    dv01 = dv01_per_million(stop) * award
    return dv01 * ((stop - hedge_yield) * 1e4 - cost_bp)


# ---- March 2020: the Fed's Treasury holdings -----------------------------------------------------

def fed_treasuries() -> list[tuple[dt.date, float]]:
    path = pathlib.Path(__file__).resolve().parents[4] / "data/markets-2/treast_2020.csv"
    with open(path) as f:
        return [(dt.date.fromisoformat(r["observation_date"]), float(r["TREAST"]) / 1e3) for r in csv.DictReader(f)]
