import numpy as np


def clean(q, window=20, limit=0.05):
    q = q[(q.bid > 0) & (q.ask > q.bid)]                   # bad sides, locked, crossed
    q = q.sort_values(["symbol", "t"], kind="stable")
    q = q.drop_duplicates(["symbol", "t"], keep="last")
    q = q.assign(mid=(q.bid + q.ask) / 2)
    past = q.groupby("symbol").mid.transform(              # the past only: no centring
        lambda s: s.rolling(window, min_periods=5).median().shift(1))
    return q[~((q.mid / past - 1).abs() > limit)]          # NaN compares false: kept


def minute_returns(q, stale_minutes=5):
    q = q.assign(day=q.t.dt.normalize()).set_index("t")
    keys = ["symbol", "day"]
    last = q.groupby(keys).mid.resample("1min", label="right", closed="left").last()
    filled = last.groupby(level=keys).ffill(limit=stale_minutes)
    return np.log(filled).groupby(level=keys).diff()       # never across a night
