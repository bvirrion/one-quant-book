"""Numbers gate: every numerical answer printed in Book 2, Chapter 20 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/settlerisk"))
from firm_settlerisk import exposure_at
from settle_demo import BOOK, TIMES, net_by_counterparty, profiles, summary

S = summary()
P = profiles()


def test_text():
    assert round(S["gross_turnover"] / 1e9, 2) == 1.53 and round(S["peak_gross"] / 1e9, 2) == 1.33
    assert round(S["net_payments"] / 1e6) == 430 and round(S["peak_net"] / 1e6) == 430
    assert round(S["peak_pvp"] / 1e6) == 30 and S["herstatt_hours"] == 23.0
    assert round((5.2 + 7.6 + 1.4), 1) == 14.2 and round(1.4 / 14.2 * 100) == 10


def test_exercises():
    g, n = dict(P["gross"]), dict(P["net"])
    assert [round(g[t] / 1e6) for t in (5.0, 8.0, 14.0, 17.0)] == [330, 930, 1330, 730]
    assert [round(n[t] / 1e6) for t in (5.0, 8.0, 14.0, 17.0)] == [130, 330, 430, 230]
    net = {(t.counterparty, t.sell, t.buy): round(t.value_usd / 1e6) for t in net_by_counterparty(BOOK)}
    assert net == {("A", "EUR", "USD"): 100, ("B", "JPY", "USD"): 100, ("C", "EUR", "GBP"): 100,
                   ("C", "USD", "GBP"): 100, ("D", "EMC", "USD"): 30}


def test_problem():
    a = [t for t in BOOK if t.counterparty == "A"]
    assert round(exposure_at(14.0, a, TIMES) / 1e6) == 700
    an = [t for t in net_by_counterparty(BOOK) if t.counterparty == "A"]
    assert round(exposure_at(14.0, an, TIMES) / 1e6) == 100
    top = [t for t, v in P["gross"] if v == S["peak_gross"]]
    assert top[0] == 13.0 and top[-1] < 16.0
