"""Numbers gate: every numerical answer printed in Book 7, chapter 10 (text and solutions)."""
import pathlib
import sys
from dataclasses import replace

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "leadlag"))
from firm_leadlag import peer_relative
from rs_leadlag import (
    LINKS,
    ccf,
    customer_momentum,
    event_study,
    interval_table,
    lead_recovery,
    mining,
    size_table,
)


def r(x, d=2):
    return round(float(x), d)


def test_size_quintiles():
    t = size_table().set_index(["weighting", "start", "freq"])
    w = [t.loc[("EW", y, "weekly")] for y in (1962, 1988, 2007)]
    assert [r(x.small_on_big) for x in w] == [0.31, 0.23, 0.06]
    assert [r(x.big_on_small) for x in w] == [0.06, -0.09, -0.05]
    assert r(w[0].own_small) == 0.37
    assert [r(x.partial_t, 1) for x in w] == [1.9, -0.7, 1.1]
    d = [t.loc[("EW", y, "daily")] for y in (1962, 2007)]
    assert (r(d[0].partial_t, 1), r(d[1].partial_t, 1)) == (13.4, -4.4)


def test_links():
    m = customer_momentum()
    assert m["months"] == 107 and 0.25 < m["n_suppliers"] / m["n_listings"] < 0.35
    assert (r(m["raw"], 3), r(m["ic_t"], 1), r(m["truth"], 3), r(m["peer"], 3)) == (0.035, 5.6, 0.074, 0.036)
    assert (r(100 * m["spread"]), r(m["sharpe"], 1)) == (0.90, 1.9)
    win, ev = event_study()
    assert (ev["n_customer"], ev["n_supplier"]) == (11_100, 9_654)
    assert r(100 * ev["customer"][win == 0][0], 1) == 4.5 and r(100 * ev["supplier"][win == 21][0]) == 0.39
    for d, want in ((5, (0.008, 1.4, 0.082)), (63, (0.031, 4.8, 0.050))):
        v = customer_momentum(replace(LINKS, link_days=d))
        assert (r(v["raw"], 3), r(v["ic_t"], 1), r(v["truth"], 3)) == want


def test_mining():
    m = mining()
    assert (m["names"], m["pairs"], m["links"]) == (698, 486_506, 133)
    assert m["daily"] == {100: 0, 1000: 0, 10_000: 3} and m["monthly"] == {100: 0, 1000: 2, 10_000: 8}
    assert (r(10_000 * 133 / 486_506, 1), r(1000 * 133 / 486_506), r(100 * 133 / 486_506)) == (2.7, 0.27, 0.03)
    assert (r(m["monthly_true_mean"], 3), r(m["monthly_sd"], 3)) == (0.052, 0.097)


def test_pair():
    c = ccf(0.5)
    assert (c["argmax"], c["centre"], r(c["llr"]), r(c["changes_per_s"])) == (0.15, 0.5, 1.17, 0.65)
    assert r(ccf(0.0)["llr"]) == 1.03 and r(ccf(0.5, 0.12)["changes_per_s"]) == 0.16
    rec = lead_recovery()
    fast = [(a - L, c - L) for L, v in rec[1.0].items() for a, c in v]
    assert (r(np.mean([abs(c) for _, c in fast]), 3), r(max(abs(c) for _, c in fast), 2)) == (0.053, 0.2)
    assert (r(np.mean([abs(a) for a, _ in fast])), r(max(abs(a) for a, _ in fast), 2)) == (0.19, 0.5)
    slow = [abs(c - L) for L, v in rec[0.12].items() for _, c in v]
    assert np.mean(slow) > 0.5
    t = interval_table()
    rows = [[r(t[d][k]) for d in (0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0)] for k in ("a_to_b", "b_to_a", "own_b")]
    assert rows == [[0.12, 0.39, 0.55, 0.59, 0.48, 0.26, -0.02], [0.11, 0.33, 0.43, 0.45, 0.31, 0.16, -0.04],
                    [0.13, 0.31, 0.40, 0.44, 0.35, 0.22, -0.03]]
    assert [r(t[d]["a_to_b"] - t[d]["b_to_a"]) for d in (2.0, 5.0, 10.0, 30.0)] == [0.13, 0.17, 0.10, 0.02]
    assert r(t[2.0]["a_to_b"] - t[2.0]["own_b"]) == 0.14


def test_exercises():
    x = np.array([[0.01, 0.02, 0.03, 0.04, 0.10]])
    loo = peer_relative(x, np.zeros(5, int))[0, 4]
    assert (r(100 * loo, 1), r(100 * (0.10 - x.mean()), 1)) == (7.5, 6.0)
    assert abs((0.10 - x.mean()) - 4 / 5 * loo) < 1e-12
    assert (r(0.1 * -6, 1), r(0.1 * -6 / 21, 3)) == (-0.6, -0.029)
