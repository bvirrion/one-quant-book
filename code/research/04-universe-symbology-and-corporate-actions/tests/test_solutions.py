"""Numbers gate: every numerical answer printed in Book 7, chapter 4 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from rs_universe import market, split_factor_today, summary, ticker_file, ticker_panel

S = summary()


def r(x, d=1):
    return round(float(x), d)


def test_market():
    assert (S["listings"], S["delistings"], S["performance"], S["mergers"]) == (1471, 471, 113, 358)
    assert (S["splits"], S["leak"]["n_split_names"], S["reused_tickers"], S["tickers"]) == (335, 231, 158, 1549)


def test_ticker_file():
    sp = S["spurious"]
    assert sp["n_spurious"] == 164 and round(100 * sp["mean_abs_spurious"]) == 164
    assert round(100 * sp["median_abs_spurious"]) == 71 and r(100 * S["spliced_windows"], 2) == 0.30
    rows = ticker_file(market())["KMKN"]
    last_old = max((t, c) for t, p, c in rows if p == rows[0][1])
    first_new = min((t, c) for t, p, c in rows if p != rows[0][1])
    assert (last_old[0], r(last_old[1], 2), first_new[0], r(first_new[1], 2)) == (36, 4.23, 39, 39.55)
    assert round(100 * (first_new[1] / last_old[1] - 1)) == 835 and round(100 * (39.55 / 4.23 - 1)) == 835


def test_floor_and_churn():
    lk = S["leak"]
    assert (r(100 * lk["share_wrong"], 2), round(100 * lk["fwd_wrong"]), round(100 * lk["fwd_all"])) == (0.34, 71, 15)
    assert (r(100 * S["churn_plain"]), r(100 * S["churn_buffer"])) == (11.5, 3.1)
    m = market()
    adj = m["close"] / split_factor_today(m)
    assert (r(m["close"][0, 74], 2), r(adj[0, 74], 2)) == (8.65, 4.32)
    assert [(t, k) for t, p, k in m["splits"] if p == 74] == [(57, 2)]


def test_exercises():
    assert 12 / 3 == 4 and round(24 / 0.80 - 1, 2) == 29
    assert r(100 * 12 * 0.115 * 2 * 0.002, 2) == 0.55 and r(100 * 12 * 0.031 * 0.004, 2) == 0.15
    assert r(100 * 0.02 * 0.30) == 0.6
    lo, hi = ticker_panel(market(reuse_prob=0.7))[2], market(reuse_prob=0.0)["sm"].reused()
    assert hi == {} and lo["n_spurious"] == 398 and round(100 * lo["mean_abs_spurious"]) == 259
    assert round(100 * lo["median_abs_spurious"]) == 90 and len(market(reuse_prob=0.7)["sm"].reused()) == 371
