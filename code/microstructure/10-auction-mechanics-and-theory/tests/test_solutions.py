"""Numbers gate: every numerical answer printed in Book 10, chapter 10 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_auction import auction_study, close_session, race_study  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


def test_closing_auction():
    a = auction_study()
    assert [r(x) for x in a["gap"]] == [4.7, 3.5, 2.2, 1.0, 0.0, 0.0]
    assert [r(100 * x, 0) for x in a["arrive"]] == [2.0, 76.0, 89.0, 95.0, 99.0, 100.0, 100.0]
    fx = [r(a[(0.0, t)]["impact"]) for t in (60.0, 10.0, 1.0)]
    rd = [r(a[(30.0, t)]["impact"]) for t in (60.0, 10.0, 1.0)]
    assert (fx, rd) == ([3.0, 3.5, 4.7], [3.0, 3.5, 3.7])
    assert (r(a[(0.0, 1.0)]["impact"] - a[(0.0, 60.0)]["impact"], 2), r(a[(30.0, 1.0)]["impact"]
                                                                         - a[(30.0, 60.0)]["impact"], 2)) == (1.75, 0.75)
    assert [r(a[(e, t)]["impact_se"]) for e, t in ((0.0, 60.0), (0.0, 1.0), (30.0, 1.0))] == [0.6, 0.4, 0.6]
    s = close_session(1)
    assert (s["final"][1], s["final"][2]) == (1_001_900, 24_100)


def test_race():
    rc = race_study()
    assert [r(100 * rc[(iv, 200.0, 50.0)], 2) for iv in (0.0, 1.0, 10.0, 100.0)] == [99.75, 11.75, 1.25, 0.25]
    assert [r(100 * rc[(iv, 1050.0, 50.0)], 2) for iv in (0.0, 1.0, 10.0, 100.0)] == [99.75, 99.75, 11.0, 0.75]


def test_exercises():
    # 1: an uncross by hand (Book 1's firm.auction): buys 300 at market, 200 at 10.02, 400 at 10.00; sells 500 at
    # 10.00, 300 at 10.01, 200 at 10.03 (prices in cents)
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "auction"))
    from firm_auction import AuctionOrder, uncross
    orders = [AuctionOrder("b1", 1, 300, None, 1), AuctionOrder("b2", 1, 200, 1002, 2), AuctionOrder("b3", 1, 400, 1000, 3),
              AuctionOrder("s1", -1, 500, 1000, 4), AuctionOrder("s2", -1, 300, 1001, 5), AuctionOrder("s3", -1, 200, 1003, 6)]
    u = uncross(orders, 1000)
    assert (u.price, u.volume, u.surplus) == (1001, 500, -300)
    # 3: batch interval against a latency gap
    assert (r(150 / 1000, 2), r(150 / 10_000, 3), r(1000 / 10_000, 2)) == (0.15, 0.015, 0.1)
