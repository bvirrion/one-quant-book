import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_auctionmm as am  # noqa: E402


def test_book_and_impact():
    b = am.ClosingBook(p0=100, levels=10, d0=10, paired=100)
    # no imbalance: the paired interest crosses at the reference
    assert am.close_price(b, 0)[0] == 100
    # a buy imbalance of 30 needs the sell limits at 101 (10) and 102 (20): close at 102
    assert am.close_price(b, 30)[0] == 102 and am.close_price(b, -30)[0] == 98
    curve = am.impact_curve(b, [10, 30, 60, 100])
    assert curve == sorted(curve) and curve[0] == 1


def test_provider_moves_the_close_and_earns_the_reversal():
    b = am.ClosingBook(p0=100, levels=10, d0=10, paired=100)
    p, f = am.close_price(b, 60, q=30, k=0)
    assert f == 30 and p < am.close_price(b, 60)[0]
    r0 = am.provider(b, 60, 30, 0, perm=0.0)
    r1 = am.provider(b, 60, 30, 0, perm=1.0)
    assert r0["pnl"] == 30 * (p - 100) and r1["pnl"] < r0["pnl"]
    best = am.best_offer(b, 60, 0.0, [10, 20, 30, 40, 60], [0, 1, 2])
    assert best["pnl"] >= r0["pnl"]


def test_publications_converge():
    pubs = am.publications(100000, times=(600, 60, 1), seed=1)
    assert abs(pubs[-1] - 100000) < abs(pubs[0] - 100000) or abs(pubs[-1] - 100000) < 2000
