"""Numbers gate: every numerical answer printed in Book 10, chapter 3 (text and solutions)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_facts import (  # noqa: E402
    cancel_rates,
    day,
    fleeting_share,
    intraday_mean,
    lifetable,
    midas_lifetimes,
    midas_yearly,
    relative_prices,
    resilience,
    spread_profile,
    spread_vs_vol,
    spread_vs_vol_zi,
)


def r(x, d=2):
    return round(float(x), d)


def test_midas():
    m = midas_lifetimes()
    assert [r(100 * x, 0) for x in m[("large", "cancel")]] == [23, 37, 54, 74, 89, 95]
    assert [r(100 * x, 0) for x in m[("small", "cancel")]] == [13, 24, 37, 49, 66, 78]
    assert r(100 * m[("large", "trade")][5], 0) == 15
    y = midas_yearly()
    assert (y[2012]["hidden_rate"], y[2026]["hidden_rate"], y[2012]["oddlot_rate"], y[2026]["oddlot_rate"]) == (
        10.47, 32.2, 19.22, 68.38)
    assert (y[2012]["cancel_to_trade"], y[2026]["cancel_to_trade"], y[2026]["days"]) == (19.79, 16.62, 123)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_simulated_day():
    d = day()
    assert (len(d.msgs), len(d.trades)) == (715_054, 21_993)
    rp = relative_prices(d)
    assert (r(100 * rp["improve"], 1), r(100 * rp["at_best"], 1), r(100 * rp["tail"][4], 1), rp["max"]) == (
        0.5, 18.6, 40.1, 9)
    c = cancel_rates(d)
    assert [r(x, 3) for x in c[:3]] == [0.09, 0.057, 0.044]
    sp = spread_profile(d)
    assert (r(100 * sp["one"], 1), r(sp["mean"], 3)) == (96.6, 1.042)
    assert [r(100 * x, 1) for x in lifetable(d)] == [0.0, 0.1, 0.8, 6.8, 40.0, 93.5]
    assert r(100 * fleeting_share(d), 1) == 11.5
    rs = resilience(d)
    assert (rs["events"], r(rs["median"]), r(100 * rs["within_1s"], 1)) == (750, 0.19, 92.4)
    assert r((d.msgs["kind"] == b"X").sum() / len(d.trades), 1) == 15.5


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_intraday_and_spreads():
    p = intraday_mean()
    v = [x["volume"] for x in p]
    assert (round(v[0] / 1000, 1), round(min(v) / 1000, 1), round(v[-1] / 1000, 1)) == (92.2, 24.7, 55.6)
    zi = spread_vs_vol_zi()
    assert (r(zi["slope"]), r(zi["intercept"]), r(zi["r2"], 3)) == (1.64, 0.96, 0.989)
    tp = spread_vs_vol()
    assert (r(tp["r2"]), r(tp["slope"])) == (0.48, 0.19)
    assert r(max(s for s, _ in tp["points"]), 2) == 1.08


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_exercises():
    # exercise 2: a spread of two ticks, volatility per trade 0.9 ticks: the ZI fit predicts 0.96 + 1.64 * 0.9
    assert r(0.96 + 1.64 * 0.9, 2) == 2.44
    # exercise 4: 54% of cancels within 100 ms: of 1,000 cancellations, 540
    assert round(1000 * midas_lifetimes()[("large", "cancel")][2]) == 540


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_exercise_7():
    e = lifetable(day(), event=b"E")
    assert [r(100 * x, 1) for x in e[3:]] == [1.8, 4.6, 12.4]
    m = midas_lifetimes()[("large", "trade")]
    assert [r(100 * x, 1) for x in m[3:]] == [3.4, 8.7, 15.0]


def test_small_runs():
    # Half an hour of the simulated day instead of six and a half hours: each measure of the book is computed.
    d = day(seconds=1800.0)
    c = cancel_rates(d)
    assert len(c) == 6 and all(0 <= x < float("inf") for x in c)
    assert 0 <= fleeting_share(d) <= 1 and relative_prices(d) and spread_profile(d)
