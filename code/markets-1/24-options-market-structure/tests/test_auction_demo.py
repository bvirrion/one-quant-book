import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from auction_demo import compare_rules, simulate_auctions


def test_three_rules():
    r = compare_rules(115)
    assert r["customer"]["C1"] == 10 and r["customer"]["C2"] == 5 and r["pro_rata"]["C2"] == 1
    assert r["entitled"]["DMM"] == 40 > r["customer"]["DMM"] == 20


def test_competition_takes_the_order_away_from_the_initiator():
    quiet, _ = simulate_auctions(3000, 1.0, 0.0, 1)
    busy, imp = simulate_auctions(3000, 3.0, 0.6, 1)
    assert quiet > 0.55 and busy < 0.25 and imp > 0.6
    none, imp0 = simulate_auctions(500, 0.0, 0.5, 1)
    assert none == 1.0 and imp0 == 0.0
