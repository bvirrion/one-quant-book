"""Numbers gate: every number printed in Book 14, chapter 20 (text and solutions)."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_api as a  # noqa: E402

cf, frl = a.cf, a.frl


def test_shards_and_limits():
    assert a.plan() == {"connections": 5, "addresses": 1, "streams_per_conn": 160}
    assert cf.plan_shards(800, a.LIMITS)["connections"] == 1
    assert cf.plan_shards(800, a.LIMITS, 160, reconnect_window_s=10)["addresses"] == 1
    assert cf.plan_shards(800, a.LIMITS, 20, reconnect_window_s=10) == {"connections": 40, "addresses": 4, "streams_per_conn": 20}
    assert 6000 // 250 == 24 and 300 * 10 / 300 == 10


def test_resync_table():
    rows = {(r["lost"], r["depth"]): r for r in a.resync_rows((5,))}
    f, s = rows[(5, "5000 levels")], rows[(5, "1000 levels")]
    assert (f["hit"], round(f["per_symbol_s"], 1), round(f["per_conn_s"]), round(f["per_conn_done_s"], 1)) == (5, 0.5, 5769, 180.1)
    assert (round(s["per_conn_s"], 1), round(s["per_conn_done_s"], 1)) == (11.2, 0.2)
    rules = frl.binance_like().rules
    ok = [w for w in range(40, 120) if cf.resync_staleness(80, w, rules)["done_ms"] < 60000]
    assert max(ok) == 75 and 80 * 75 == 6000


def test_gap_budget_skew():
    assert a.gap_demo() == ["applied", "applied", "gap"]
    assert a.budget() == {"market making": 3300.0, "arbitrage": 2200.0, "risk": 500}
    est, true = a.skew_series()
    err = max(abs(e - t) for (_, e), (_, t) in zip(est, true, strict=True))
    assert round(1000 * err) == 15 and (round(est[0][1], 2), round(est[-1][1], 2)) == (-2.23, -4.20)


def test_small_runs():
    assert a.symbols_hit(5, 80) == 5
