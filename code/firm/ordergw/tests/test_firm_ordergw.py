import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_ordergw as gw  # noqa: E402
import firm_ordergw_sim as sim  # noqa: E402
import make_ordergw_fixtures as mk  # noqa: E402

DATA = HERE / "data"


def invariants(g):
    pos = 0
    for o in g.orders.values():
        assert 0 <= o.filled <= o.qty, o
        assert o.leaves >= 0 and o.worst_leaves() >= o.leaves
        pos += o.filled if o.side == "B" else -o.filled
    assert pos == g.position
    assert g.worst_long() >= g.position and g.worst_long() >= g.naive_long()


def test_state_table_is_closed_and_has_no_way_out_of_a_terminal_state():
    for (s, e), n in gw.TABLE.items():
        assert s in gw.STATES and e in gw.EVENTS and n in gw.STATES
        if s in gw.TERMINAL:
            assert n == s
    with pytest.raises(KeyError):
        gw.transition("cancelled", "fill")


def test_token_bucket():
    b = gw.TokenBucket(1000, 2)                          # 1,000 a second, burst 2
    assert [b.allow(t) for t in (0, 0, 0)] == [True, True, False]
    assert b.allow(1_000_000) and not b.allow(1_000_000)  # one token per millisecond


def test_fixtures_replay_to_the_expected_summaries():
    want = dict(line.split(" ", 1) for line in (DATA / "expected.txt").read_text().splitlines())
    for name, kw in mk.RUNS.items():
        lines = (DATA / f"journal_{name}.txt").read_text().splitlines()
        g = gw.replay(lines, kw.get("rate", 10_000), kw.get("burst", 100), check=invariants)
        assert gw.summary(g) == want[name]


@pytest.mark.parametrize("seed", range(8))
def test_random_interleavings_against_the_engine(seed):
    """Random latencies and fill intensities: the invariants hold after every line and the gateway agrees with the
    drop copy."""
    lat = [5_000, 50_000, 300_000, 2_000_000][seed % 4]
    for mode in ("cancel", "replace"):
        r = sim.run(seed, lat, [50.0, 400.0][seed % 2], 120, mode=mode)
        gw.replay(r.journal, check=invariants)
        assert gw.reconcile(r.gateway, r.drop_copy) == []


def test_worst_case_limit_holds_against_the_engine():
    for seed in range(4):
        r = sim.run(seed, 500_000, 400.0, 60, max_long=100)
        assert r.max_position <= 100


def test_naive_accounting_doubles_the_position():
    """Cancel an order and send its replacement at once: a fill crosses the cancel; a gateway that counts only live,
    acknowledged orders let both fill, while worst-case accounting refuses the second order."""
    naive = gw.Gateway(max_long=10**9)
    naive.new(0, 1, "B", 100, 1000)
    naive.on_report(10, "A", 1)
    naive.cancel(20, 1)
    assert naive.naive_long() == 0                        # it believes the old order is gone
    assert naive.new(21, 2, "B", 100, 1000)[0] == "send"
    naive.on_report(30, "E", 1, qty=100, price=1000, leaves=0)   # the fill that crossed the cancel
    naive.on_report(31, "J", 1, reason="L")
    naive.on_report(40, "A", 2)
    naive.on_report(50, "E", 2, qty=100, price=1000, leaves=0)
    assert naive.position == 200 and naive.races == 1
    safe = gw.Gateway(max_long=100)
    safe.new(0, 1, "B", 100, 1000)
    safe.on_report(10, "A", 1)
    safe.cancel(20, 1)
    assert safe.worst_long() == 100 and safe.new(21, 2, "B", 100, 1000) == ("refused", "exposure")


def test_race_model_matches_the_engine_when_orders_live_long():
    r = sim.run(3, 100_000, 200.0, 3000)
    frac = r.gateway.races / r.cancels
    assert abs(frac - sim.race_probability(200.0, 100_000)) < 0.01
