"""Acceptance tests of the Book 2, Chapter 4 build (uniform-price auction)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_tsyauction import Bid, cap_bids, coupon_from_high_yield, run_auction, tail_bp


def test_everybody_pays_the_stop_out():
    bids = [Bid("a", 0.0410, 30), Bid("b", 0.0412, 30), Bid("c", 0.0415, 30), Bid("d", 0.0415, 30)]
    r = run_auction(100, 0, bids)
    assert r.stop == 0.0415 and r.allotment_at_stop == pytest.approx(0.6667)   # rounded up to 0.01%
    assert r.awards == pytest.approx({"a": 30, "b": 30, "c": 20.001, "d": 20.001})
    assert sum(r.awards.values()) == pytest.approx(100, abs=0.01)


def test_noncompetitive_first_and_bid_to_cover():
    bids = [Bid("a", 0.0410, 30), Bid("b", 0.0411, 30), Bid("c", 0.0412, 30), Bid("d", 0.0413, 30)]
    r = run_auction(100, 10, bids)
    assert r.stop == 0.0412 and r.allotment_at_stop == pytest.approx(1.0)      # 90 filled exactly
    r2 = run_auction(100, 12, bids)
    assert r2.stop == 0.0412 and r2.allotment_at_stop == pytest.approx(0.9334)
    assert r.bid_to_cover == pytest.approx((120 + 10) / 100)


def test_thirty_five_percent_cap():
    capped = cap_bids([Bid("big", 0.0410, 50), Bid("big", 0.0411, 20)], 100)
    assert sum(b.amount for b in capped) == pytest.approx(35)
    assert capped[0].amount == 35


def test_uncovered_auction_raises():
    with pytest.raises(ValueError):
        run_auction(100, 0, [Bid("a", 0.04, 50)])


def test_tail_sign():
    assert tail_bp(0.04195, 0.04180) == pytest.approx(1.5)
    assert tail_bp(0.04170, 0.04180) == pytest.approx(-1.0)


def test_coupon_rounds_down_to_an_eighth():
    assert coupon_from_high_yield(0.04198) == 4.125
    assert coupon_from_high_yield(0.04250) == 4.25
    assert coupon_from_high_yield(0.00050) == 0.125
