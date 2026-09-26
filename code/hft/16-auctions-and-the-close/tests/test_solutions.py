"""Numbers gate: every numerical answer printed in Book 11, chapter 16 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_auction as h  # noqa: E402

am = h.am


def r(x, d=2):
    return round(float(x), d)


def test_impact_and_offers():
    assert h.impact() == {25000: 5, 50000: 7, 100000: 10, 200000: 14, 300000: 17, 400000: 20}
    o = h.offers()
    assert [r(o[(i, 0.15)]["per_share"]) for i in h.IMBALANCES] == [2.25, 2.95, 4.5, 6.9, 8.45, 10.0]
    assert [r(o[(200000, p)]["per_share"]) for p in h.PERMS] == [8.0, 6.9, 4.0]
    assert o[(200000, 0.5)]["q"] == 80000
    w = h.with_provider()
    assert (w["close_move"], w["alone_move"], w["q"], w["k"], r(w["pnl"] / 100)) == (9, 14, 120000, 0, 8280.0)


def test_late_orders():
    x = h.late()
    assert r(x["known"]["per_share"], 1) == 6.9 and r(x["same_offer"]["per_share"], 1) == 5.5
    assert (x["best"]["q"], x["best"]["k"], r(x["best"]["per_share"], 1)) == (120000, 4, 6.0)


def test_exercises():
    toy = [am.fa.AuctionOrder("s1", -1, 10, 101, 0), am.fa.AuctionOrder("s2", -1, 20, 102, 1),
           am.fa.AuctionOrder("s3", -1, 30, 103, 2), am.fa.AuctionOrder("b", 1, 30, None, 3)]
    assert am.fa.uncross(toy, 100).price == 102
    d = h.deeper()
    assert (d["move"], d["q"], d["k"], r(d["per_share"], 1)) == (10, 100000, 0, 5.5)
    assert r(9 - 0.15 * 14, 1) == 6.9
