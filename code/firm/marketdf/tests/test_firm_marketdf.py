"""Acceptance tests of firm.marketdf (One Quant Book 15, chapter 10): three engines, one answer, edge cases included."""
import pathlib
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_marketdf import ENGINES, asof, bars, rolling_mean, to_long, to_wide, xs_rank

S = 10**9


def ticks(n=3000, seed=1):
    rng = np.random.default_rng(seed)
    ts = np.sort(rng.integers(0, 3600, n)) * S                      # whole seconds: ties and boundary trades
    return pd.DataFrame({"seq": np.arange(n), "symbol": rng.choice(["A", "B"], n), "ts": ts,
                         "price": 10_000 + rng.integers(-50, 50, n) * 100, "qty": rng.integers(1, 10, n) * 100})


@pytest.mark.parametrize("label,closed,fill", [("left", "left", False), ("right", "right", False),
                                               ("left", "left", True), ("right", "left", True)])
def test_bars_agree_across_engines(label, closed, fill):
    t = ticks()
    ref = bars(t, 60 * S, label, closed, fill, "pandas")
    for e in ENGINES[1:]:
        pd.testing.assert_frame_equal(bars(t, 60 * S, label, closed, fill, e), ref)
    assert ref.groupby("symbol")["volume"].sum().to_dict() == t.groupby("symbol")["qty"].sum().to_dict()


def test_bars_conventions_by_hand():
    t = pd.DataFrame({"seq": [0, 1, 2, 3], "symbol": "A", "ts": [0, 60 * S, 61 * S, 200 * S],
                      "price": [1, 2, 3, 4], "qty": [10, 20, 30, 40]})
    left = bars(t, 60 * S, "left", "left")
    right = bars(t, 60 * S, "right", "right")
    assert left["bar"].tolist() == [0, 60 * S, 180 * S] and left["volume"].tolist() == [10, 50, 40]
    assert right["bar"].tolist() == [0, 60 * S, 120 * S, 240 * S] and right["volume"].tolist() == [10, 20, 30, 40]
    filled = bars(t, 60 * S, fill=True)
    assert filled["bar"].tolist() == [0, 60 * S, 120 * S, 180 * S]
    assert filled.loc[2, ["volume", "open", "close"]].tolist() == [0, 3, 3]


def test_asof_rolling_and_rank_agree():
    t = ticks()
    q = t.assign(bid=t["price"] - 100)[["symbol", "ts", "bid"]].drop_duplicates(["symbol", "ts"], keep="last")
    tr = t[["symbol", "ts", "qty"]].iloc[::7].drop_duplicates(["symbol", "ts"])
    for strict in (False, True):
        ref = asof(tr, q, strict=strict)
        for e in ENGINES[1:]:
            got = asof(tr, q, engine=e, strict=strict)
            assert got["bid"].fillna(-1).astype(int).tolist() == ref["bid"].fillna(-1).astype(int).tolist()
    ref = rolling_mean(t, "symbol", "ts", "price", 5)
    for e in ENGINES[1:]:
        assert np.allclose(rolling_mean(t, "symbol", "ts", "price", 5, e), ref)
    b = bars(t, 60 * S)
    ref = xs_rank(b, "bar", "close")
    for e in ENGINES[1:]:
        assert np.allclose(xs_rank(b, "bar", "close", e), ref)


def test_pivot_round_trip():
    b = bars(ticks(), 60 * S)
    w = to_wide(b, "bar", "symbol", "close")
    back = to_long(w, "bar", "symbol", "close")
    assert back["close"].astype(int).tolist() == b.sort_values(["bar", "symbol"])["close"].tolist()
