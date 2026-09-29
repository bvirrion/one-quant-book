"""Numbers gate: every number printed in Book 14, chapter 26 (text and solutions)."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_power as n  # noqa: E402

pl = n.pl


def test_race():
    assert (round(100 * n.share(2.0), 1), round(100 * n.share(10.0), 1)) == (98.5, 4.5)
    assert round(100 * n.share(10.0, 3), 1) == 95.4
    assert (round(100 * n.share(4.9), 1), round(100 * n.share(5.0), 1)) == (51.3, 49.3)
    assert (round(n.value(2.0), 2), round(n.value(10.0), 2)) == (11.82, 0.54)
    assert [r.median_ms for r in n.RIVALS] == [5, 10, 20, 40, 80]


def test_betfair():
    p = n.polling()
    assert (p["EX_BEST_OFFERS"]["per_request"], p["EX_BEST_OFFERS"]["requests_s"]) == (40, 125)
    assert (p["EX_ALL_OFFERS+EX_TRADED"]["per_request"], p["EX_ALL_OFFERS+EX_TRADED"]["requests_s"]) == (6, 835)
    assert p["EX_BEST_OFFERS"]["stale_ms"] == 110.0 and 1000 // 40 == 25
    assert n.transactions() == (7200, 2200)
    assert 3000 + 500 == 3500 and pl.charged_transactions(3500) == 0


def test_small_runs():
    assert pl.gate_closure(600, 30) == 570
    r = pl.capacity_race((pl.Participant("a", 1.0), pl.Participant("b", 100.0)), n=500)
    assert r["a"] > 0.99
