import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_gwmodel as gm  # noqa: E402


def test_segment_is_fair_and_copies_do_not_help():
    d = gm.Design(kind="segment")
    p1, _, _ = gm.win_rate(d, 1, others=3, n=4000)
    p4, _, _ = gm.win_rate(d, 4, others=3, n=4000)
    assert abs(p1 - 0.25) < 0.03 and abs(p4 - 0.25) < 0.03


def test_parallel_copies_help():
    d = gm.Design()
    p1, _, b1 = gm.win_rate(d, 1, others=3, n=3000)
    p4, _, b4 = gm.win_rate(d, 4, others=3, other_sessions=4, n=3000)
    q4, _, _ = gm.win_rate(d, 4, others=3, n=3000)
    assert q4 > p1 + 0.1 and b4 > b1 and abs(p4 - 0.25) < 0.03


def test_race_queue_by_hand():
    d = gm.Design(gateways=1, net_sd_us=0.0, background=0.0, service_us=1.0)
    w, t, b = gm.race(d, [1, 1], np.random.default_rng(0))
    assert (t, b) == (21.0, 23.0) and w in (0, 1)


def test_sessions_and_loss():
    full, ultra = gm.load_sessions()
    assert gm.session_cost(full, 8) == 6 * 260 + 2 * 520 and gm.session_cost(ultra, 2) == 1560
    cost, mix = gm.plan_sessions(900, (full, ultra))
    assert (cost, mix) == (1560, {"HF Full": 6, "HF Ultra": 0})
    assert gm.both_lost(0.01, 0.01) == 0.01 * 0.01 and gm.both_lost(0.01, 0.01, 1.0) == 0.01


def test_reconcile_sessions():
    a, b = gm.og.Gateway(), gm.og.Gateway()
    a.new(0, 1, "B", 5, 100)
    a.on_report(1, "A", 1)
    a.on_report(2, "E", 1, qty=5, leaves=0)
    b.new(0, 1, "B", 5, 100)
    b.on_report(1, "A", 1)
    dc = [("s1", "E", 1, 5), ("s2", "E", 1, 5), ("s3", "E", 9, 1)]
    breaks = gm.reconcile_sessions({"s1": a, "s2": b}, dc)
    assert breaks == ["session s2: order 1: gateway filled 0, drop copy 5", "session s3: in the drop copy, not in the firm"]
