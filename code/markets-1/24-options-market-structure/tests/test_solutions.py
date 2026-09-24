"""Numbers gate: every numerical answer printed in the Chapter 24 text and solutions."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from auction_demo import BOOK, OPRA_PROJECTIONS, compare_rules, simulate_auctions

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/match"))
from firm_optmatch import Quote, customer_priority_pro_rata, price_improvement_auction


def test_text():
    r = compare_rules(115)
    assert r["pro_rata"] == {"MM1": 24, "C1": 2, "DMM": 22, "F": 11, "C2": 1, "MM2": 55}
    assert r["customer"] == {"C1": 10, "C2": 5, "MM1": 20, "DMM": 20, "F": 10, "MM2": 50}
    assert r["entitled"] == {"C1": 10, "C2": 5, "DMM": 40, "MM1": 16, "F": 7, "MM2": 37}
    assert round(simulate_auctions(4000, 1.0, 0.0, 24)[0] * 100, 1) == 65.5
    assert round(simulate_auctions(4000, 3.0, 0.5, 24)[0] * 100, 1) == 12.7
    assert OPRA_PROJECTIONS[2] == ("7/2026", 311, 13.575) and round(0.05 / 3.0 * 100, 1) == 1.7


def test_exercises():
    assert customer_priority_pro_rata(BOOK, 12) == {"C1": 10, "C2": 2}
    assert 60 * 100 // 400 == 15 and 60 * 50 // 400 == 7 and 60 * 250 // 400 == 37
    assert round(0.05 / 3.10 * 100, 1) == 1.6
    avg = 311e9 / (6.5 * 3600) / 1e6
    assert round(avg, 1) == 13.3 and round(13.575 * 10, 1) == 135.8 and round(13.575 * 10 / avg, 1) == 10.2
    assert round(4.403 * 10 * 2 * 1.1) == 97
    cases = ([], [("a", 250, 100)], [("a", 250, 100), ("b", 250, 100), ("c", 250, 100)],
             [("a", 249, 60), ("b", 250, 100), ("c", 250, 100)])
    assert [price_improvement_auction(100, 250, +1, c).initiator_qty for c in cases] == [100, 50, 40, 40]
    assert round(2.50 - 0.90, 2) == 1.60 and round((2.45 - 0.95), 2) == 1.50 and round(1.60 - 1.40, 2) == 0.20
    s1, i1 = simulate_auctions(4000, 1.0, 0.5, 24)
    s3, i3 = simulate_auctions(4000, 3.0, 0.5, 24)
    assert [round(x * 100, 1) for x in (s1, i1, s3, i3)] == [47.8, 39.7, 12.7, 77.5]
    mm = [Quote("prop", 5, "firm"), Quote("mm", 450, "mm")]
    assert customer_priority_pro_rata(mm, 100) == {"prop": 2, "mm": 98} and 100 * 5 // 455 == 1


def test_problem():
    fills = [100, 50, 40, 40, 0]
    probs = [0.10, 0.25, 0.35, 0.20, 0.10]
    exp = sum(f * p for f, p in zip(fills, probs, strict=True))
    assert exp == pytest.approx(44.5) and round((2.50 - 2.44) * 100) == 6 and exp * 6 == pytest.approx(267.0)
    improve = (0.20 * 60 + 0.10 * 100) * 1.0 / 100          # dollars per contract: one cent x 100 on the improved lots
    assert improve == pytest.approx(0.22)
    assert 267.0 - 0.30 * 100 == pytest.approx(237.0)
    assert round((2.48 - 2.44) * 100) == 4
