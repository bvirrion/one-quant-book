"""Numbers gate: every numerical answer printed in Book 11, chapter 10 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_engine as h  # noqa: E402

qe = h.qe


def r(x, d=3):
    return round(float(x), d)


def test_compare():
    c = h.compare()
    one, three, hyst, thr = (c[k] for k in h.CONFIGS)
    assert [r(one[k], 3) for k in ("messages_h", "fills_h", "races_h", "markout", "edge_h")] == [757.5, 249.75, 19.5, 0.141, 35.25]
    assert [r(three[k], 3) for k in ("messages_h", "fills_h", "races_h", "markout", "edge_h")] == [980.25, 282.0, 20.25, 0.144, 40.5]
    assert [r(hyst[k], 3) for k in ("messages_h", "fills_h", "races_h", "markout", "edge_h")] == [806.25, 363.75, 1.5, -0.064, -23.25]
    assert [r(thr[k], 3) for k in ("messages_h", "fills_h", "races_h", "markout", "edge_h", "dropped_h")] == [
        883.5, 282.0, 9.75, 0.154, 43.5, 1395.75]
    assert [r(x["median_age"], 1) for x in (one, three, hyst, thr)] == [9.6, 17.3, 9.6, 17.7]
    assert [r(x["orders_per_fill"], 1) for x in (one, three, hyst, thr)] == [3.0, 3.5, 2.2, 3.1]
    assert round(100 * (three["messages_h"] / one["messages_h"] - 1)) == 29
    assert round(100 * (three["edge_h"] / one["edge_h"] - 1)) == 15


def test_fixture():
    assert h.fixture_stats() == {"new": 645, "amend": 56, "cancel": 453, "dropped": 849, "fills": 523, "races": 217}
    assert h.fixture_stats(rate=5.0, burst=2.0) == {"new": 71, "amend": 0, "cancel": 1, "dropped": 195, "fills": 1, "races": 0}
    n = sum(1 for _ in open(h.ROOT / "firm/quoteengine/data/fixture_expected.csv")) - 1
    m = sum(1 for _ in open(h.ROOT / "firm/quoteengine/data/fixture_events.csv")) - 1
    assert (n, m) == (1154, 3000)


def test_exercises():
    assert 12000 / 400 - 1 == 29
    b = qe.TokenBucket(2.0, 5.0)
    assert all(b.take(0.0) for _ in range(5)) and not b.take(0.0)
    assert sum(b.take(1.2) for _ in range(5)) == 2
    e = qe.QuoteEngine()
    (a,) = e.update(0.0, 1, [(100, 300)])
    e.ack(a[1])
    assert e.update(0.1, 1, [(100, 100)]) == [("amend", a[1], 100)]
