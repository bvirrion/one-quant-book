import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_auctionsim import ClosingAuction, batch_venue, final_cross, gap_path, indicatives  # noqa: E402
from firm_exchsim import SEC, ExchangeConfig, Order, Simulator  # noqa: E402, I001

T0 = 34_200 * SEC


def _run(policy, orders, close_s=100):
    close = T0 + close_s * SEC
    cfg = ExchangeConfig(phases=policy.phases(T0, close, close + 60 * SEC))
    sim = Simulator(cfg, seed=3)
    sim.add_events(orders=orders, controls=policy.controls("SIMX", close, 1_000_000))
    return sim.run(), close


def test_closing_call_indicatives_and_cross():
    pol = ClosingAuction(call_s=50, indicative_s=1)
    orders = [(T0 + 60 * SEC, "SIMX", Order(side="B", qty=1000, price=0, tif="C")),        # market on close
              (T0 + 70 * SEC, "SIMX", Order(side="S", qty=600, price=1_000_100, tif="C")),  # limit on close
              (T0 + 80 * SEC, "SIMX", Order(side="S", qty=600, price=1_000_300, tif="C"))]
    res, close = _run(pol, orders)
    ind = indicatives(res)
    f = final_cross(res)
    assert f[0] >= close and (f[1], f[2]) == (1_000_300, 1000)
    # nothing pairs before the first sell (no indicative); then 600 paired at 100.01 with 400 more to buy; then
    # 1,000 paired at 100.03 with 200 more to sell
    assert ind["t"][0] > T0 + 70 * SEC
    i75, i85 = (ind[np.searchsorted(ind["t"], T0 + s * SEC) - 1] for s in (75, 85))
    assert (i75["paired"], i75["imbalance"], i75["price"]) == (600, 400, 1_000_100)
    assert (i85["paired"], i85["imbalance"], i85["price"]) == (1000, -200, 1_000_300)
    g = gap_path(ind, f, [25, 10, 1])
    assert list(g) == [2.0, 0.0, 0.0]


def test_random_end_collar_and_batch():
    pol = ClosingAuction(call_s=50, random_end_s=20, collar=0.001)
    orders = [(T0 + 60 * SEC, "SIMX", Order(side="B", qty=500, price=0, tif="C")),
              (T0 + 61 * SEC, "SIMX", Order(side="S", qty=500, price=1_002_000, tif="C")),    # outside the collar
              (T0 + 62 * SEC, "SIMX", Order(side="S", qty=500, price=1_000_100, tif="C"))]
    res, close = _run(pol, orders)
    f = final_cross(res)
    assert close <= f[0] < close + 20 * SEC and f[1] == 1_000_100
    rep = res.reports("SCRIPT")
    assert any(r["type"] == "J" and r["reason"] == "B" for r in rep)
    assert batch_venue(100).batch_interval_ns == 100_000_000
