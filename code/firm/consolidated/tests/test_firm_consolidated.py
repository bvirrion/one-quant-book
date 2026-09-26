import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_consolidated import disagreement, information_shares, locked_crossed, nbbo_events, sample  # noqa: E402

TOP = np.dtype([("t", "f8"), ("bid", "i8"), ("bid_qty", "i8"), ("ask", "i8"), ("ask_qty", "i8")])


def test_nbbo_delays_and_locked_crossed():
    a = np.array([(0.0, 100, 200, 102, 200), (1.0, 101, 100, 102, 200)], dtype=TOP)
    b = np.array([(0.0, 99, 500, 103, 500), (2.0, 102, 300, 104, 100), (3.0, 99, 300, 101, 50)], dtype=TOP)
    nb = nbbo_events({"A": a, "B": b})
    assert [tuple(r)[1:] for r in nb] == [(100, 200, 102, 200), (101, 100, 102, 200), (102, 300, 102, 200),
                                        (101, 100, 102, 200)]
    lc = locked_crossed(nb, 0.0, 4.0)
    assert (lc["locked"], lc["locked_episodes"], lc["locked_median_s"], lc["crossed"]) == (0.25, 1, 1.0, 0.0)
    late = nbbo_events({"A": a, "B": b}, delays={"B": 0.5})
    assert disagreement(nb, late, 0.0, 4.0) == 0.25                   # B's update at 2 is seen at 2.5, at 3 at 3.5
    assert tuple(sample(late, [2.2])[0])[1:] == (101, 100, 102, 200)
    # the 50-share ask at 101 is an odd lot: not protected, and firm_nbbo has no NBBO without both sides
    assert tuple(nbbo_events({"B": b[2:]})[0])[1:] == (-1, 0, -1, 0)


def test_information_shares_find_the_leader():
    rng = np.random.default_rng(1)
    T = 20_000
    v = np.cumsum(rng.standard_normal(T))
    lead = v + 0.1 * rng.standard_normal(T)
    lag1 = np.concatenate([[0.0], v[:-1]]) + 0.1 * rng.standard_normal(T)
    lag3 = np.concatenate([[0.0] * 3, v[:-3]]) + 0.1 * rng.standard_normal(T)
    r = information_shares(np.column_stack([lead, lag1, lag3]), lags=5)
    assert r["is_low"][0] > 0.9 and r["is_high"][1] < 0.1 and r["is_high"][2] < 0.1
    assert r["component_share"][0] > 0.9
    assert abs(r["component_share"].sum() - 1) < 1e-9 and np.all(r["is_low"] <= r["is_high"] + 1e-12)
