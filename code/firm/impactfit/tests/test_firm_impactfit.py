import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_impactfit import aggregate, decontaminate, fit_power, metaorder_path, orders, response  # noqa: E402

TRD = np.dtype([("t", "f8"), ("price", "i8"), ("qty", "i8"), ("sign", "i1")])


def test_orders_and_response_by_hand():
    tr = np.array([(1.0, 100, 100, 1), (1.0, 101, 100, 1), (2.0, 100, 100, -1), (3.0, 101, 300, 1)], dtype=TRD)
    o = orders(tr)
    assert list(o["qty"]) == [200, 100, 300] and list(o["sign"]) == [1, -1, 1]
    times, mids = np.array([0.0, 1.5, 2.5, 3.5]), np.array([100.0, 101.0, 100.5, 102.0])
    r = response(tr, times, mids, lags=(1,), size_edges=(0, 250, 1000))
    # after the buy at 1: +1 at the next order's time (mid before order 2 is 101); after the sale at 2: -(100.5-101)
    assert r["all"][0] == np.mean([1.0, 0.5])
    assert r["by_size"][(0, 250)][0] == np.mean([1.0, 0.5])
    assert metaorder_path(times, mids, 1.0, 3.0, 1, (0.5, 1.0)).tolist() == [1.0, 0.5]


def test_aggregate_fit_and_decontamination():
    rng = np.random.default_rng(2)
    n = 5000
    t = np.sort(rng.uniform(0, 1000, n))
    q = 100 * rng.integers(1, 5, n)
    s = rng.choice([-1, 1], n)
    tr = np.zeros(n, TRD)
    tr["t"], tr["qty"], tr["sign"] = t, q, s
    mids = np.cumsum(0.002 * q * s)                    # the mid moves 0.002 a share
    a = aggregate(tr, t, mids, 10.0, [-1e9, 0, 1e9])
    assert abs(a["slope"] - 0.002) < 2e-4
    part = np.exp(rng.uniform(np.log(1e-4), np.log(0.05), 4000))
    sig = rng.uniform(0.01, 0.03, 4000)
    imp = 0.8 * sig * part**0.5 * (1 + 0.1 * rng.standard_normal(4000))
    f = fit_power(imp, sig, part, boot=50, clusters=np.arange(4000) % 40)
    assert abs(f["exponent"] - 0.5) < 0.03 and abs(f["prefactor_sqrt"] - 0.8) < 0.03
    assert f["exponent_ci"][0] < 0.5 < f["exponent_ci"][1]
    d = decontaminate([1.0, 2.0], [0.5, 1.0])
    assert d["clean"].tolist() == [0.5, 1.0] and abs(d["beta"] - 2.0) < 1e-12
