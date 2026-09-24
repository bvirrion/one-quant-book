"""Acceptance tests of the Book 3, Chapter 16 build (arbitrage scanner)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_triarb import Quote, cross, scan, triangular

BOOK = {"BTC/USDT": Quote(60_000, 60_001, 2, 2), "ETH/USDT": Quote(3_000, 3_000.3, 50, 50),
        "ETH/BTC": Quote(0.04990, 0.04991, 40, 40)}


def test_triangular_both_directions():
    o1, o2 = triangular(BOOK, "BTC", "ETH", "USDT", 0.0)
    # USDT>BTC>ETH>USDT: 3000/(60001*0.04991) - 1
    assert round(o1.edge_bp, 2) == round(1e4 * (3000 / (60_001 * 0.04991) - 1), 2) and o1.edge_bp > 0
    assert o2.edge_bp < 0
    assert triangular(BOOK, "BTC", "ETH", "USDT", 0.001)[0].edge_bp < 0      # fees kill it


def test_cross_and_transfer_risk():
    a, b = Quote(59_990, 60_000, 1, 1), Quote(60_300, 60_310, 1, 1)
    o = cross(a, b, 0.001, 0.001, "A>B")
    assert round(o.edge_bp, 1) == round(1e4 * (60_300 * 0.999 - 60_000 * 1.001) / 60_150, 1)
    slow = cross(a, b, 0.001, 0.001, "A>B", transfer_minutes=60, vol_annual=0.6, z=1.65)
    assert slow.edge_bp < o.edge_bp - 100


def test_scan_sorted_and_filtered():
    books = {"X": BOOK, "Y": {"BTC/USDT": Quote(60_200, 60_210, 1, 1)}}
    found = scan(books, {"X": 0.0, "Y": 0.0}, [("BTC", "ETH", "USDT")], rebalance_bp=5)
    assert [o.route for o in found] == ["USDT>BTC>ETH>USDT", "BTC/USDT X>Y"]
    assert all(o.edge_bp > 0 for o in found)
