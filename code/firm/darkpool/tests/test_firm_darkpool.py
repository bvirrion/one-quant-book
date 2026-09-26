import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_darkpool import ConditionalBook, counterparty_markout, pre_completion_drift_bps, shortfall_bps  # noqa: E402


def test_conditionals_invite_firm_up_and_score():
    cb = ConditionalBook(firm_up_ns=100)
    b = cb.add("fund", 1, 20_000, 5_000, 0)
    s1 = cb.add("maker", -1, 3_000, 1_000, 1)          # too small for the fund's minimum: no invitation
    assert cb.invitations(2) == []
    s2 = cb.add("seller", -1, 8_000, 2_000, 3)
    (iid, bb, ss, q), = cb.invitations(4)
    assert (bb, ss, q) == (b, s2, 8_000)
    assert cb.firm_up(iid, "fund", 50) is None           # waiting for the seller
    assert cb.firm_up(iid, "seller", 60) == ("fund", "seller", 8_000)
    assert cb.orders[b].qty == 12_000 and s2 not in cb.orders
    s3 = cb.add("leaky", -1, 6_000, 1_000, 70)
    (iid2, _, _, q2), = cb.invitations(71)
    assert q2 == 6_000
    cb.firm_up(iid2, "fund", 80)
    assert cb.expire(172) == [iid2] and cb.firm_up(iid2, "leaky", 173) is None
    assert (cb.firm_up_rate("fund"), cb.firm_up_rate("seller"), cb.firm_up_rate("leaky")) == (1.0, 1.0, 0.0)
    assert math.isnan(cb.firm_up_rate("maker")) and s1 in cb.orders and s3 in cb.orders


def test_leakage_measures():
    assert math.isclose(shortfall_bps(1, [(100.05, 100), (100.15, 300)], 100.0), 12.5)
    assert math.isclose(shortfall_bps(-1, [(99.9, 100)], 100.0), 10.0)
    t, m = [0.0, 10.0, 20.0], [100.0, 100.2, 100.5]
    assert math.isclose(pre_completion_drift_bps(1, t, m, 5.0, 15.0), 20.0)
    assert math.isclose(pre_completion_drift_bps(1, t, m, 0.0, 25.0), 50.0)
    mid = lambda x: np.interp(x, [0, 100], [100.0, 101.0])  # noqa: E731
    # we bought at 100.00 at t = 0; our seller lost 0.10 a share by t = 10
    assert math.isclose(counterparty_markout(1, [(0.0, 100.0, 500)], mid, 10.0), -0.1)
