"""Numbers gate: every numerical answer printed in Book 2, Chapter 4 (text and solutions)."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/tsyauction"))
from firm_tsyauction import Bid, cap_bids, coupon_from_high_yield, run_auction, tail_bp
from tsy_auction_demo import (
    ISSUE,
    NOTE,
    OFFERING,
    WI,
    auction,
    bid_book,
    dealer_pnl,
    dv01_per_million,
    fed_treasuries,
    summary,
)

S = summary()


def test_text():
    h = dict(fed_treasuries())
    a, b = h[dt.date(2020, 3, 11)], h[dt.date(2020, 4, 15)]
    assert (round(a), round(b), round(b - a)) == (2523, 3789, 1266)
    assert (dt.date(2020, 4, 15) - dt.date(2020, 3, 11)).days == 35
    assert round(NOTE.clean_price(S["stop"], ISSUE), 3) == 99.409
    assert round(2.02 - 1.86, 2) == 0.16 and round(2.14 + 0.06, 2) == 2.20


def test_exercises():
    r = run_auction(30, 3, [Bid("a", 0.04100, 10), Bid("b", 0.04105, 8), Bid("c", 0.04110, 10), Bid("d", 0.04115, 6)])
    assert r.stop == 0.04110 and round(r.allotment_at_stop * 100, 2) == 90.00 and round(r.bid_to_cover, 2) == 1.23
    assert round(tail_bp(0.04292, 0.04285), 1) == 0.7 and round(tail_bp(0.04281, 0.04285), 1) == -0.4
    assert coupon_from_high_yield(0.04198) == 4.125 and coupon_from_high_yield(0.03999) == 3.875
    assert round(OFFERING / 26) == 1615
    assert round(sum(b.amount for b in cap_bids([Bid("z", 0.042, 20_000)], 42_000)) / 1000, 1) == 14.7
    shifted = [Bid(b.bidder, round(b.yld + 0.0001, 5) if b.bidder.startswith("I") else b.yld, b.amount)
               for b in bid_book()]
    r2 = run_auction(OFFERING, 300, shifted)
    assert round(r2.stop * 100, 3) == 4.200 and round(tail_bp(r2.stop, WI), 1) == 2.0


def test_problem():
    r = auction()
    assert OFFERING - 300 == 41_700
    assert r.awards["D07"] == 1000.0
    assert round(dv01_per_million(r.stop)) == 807 and round(dv01_per_million(r.stop) * 1000) == 806_797
    assert round(dealer_pnl(1000, r.stop, WI)) == 1_250_536
    assert round(dv01_per_million(0.04178)) == 808 and round(dealer_pnl(1000, 0.04178, WI)) == -363_758
    assert round(OFFERING / 26, 1) == 1615.4
