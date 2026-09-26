import json
import pathlib
import random
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_riskgate as rg  # noqa: E402
import firm_riskgate_runaway as ra  # noqa: E402
import make_riskgate_fixtures as mk  # noqa: E402

LIM = mk.limits()


def gate():
    g = rg.Gate(LIM[1], 0)
    g.set_reference(0, 1, 1_000_000)
    return g


def test_fixture_decisions_and_every_check_exercised():
    head, want = (HERE / "data/expected.txt").read_text().splitlines()
    ev = (HERE / "data/events.txt").read_text().splitlines()
    s, counts = rg.decisions(rg.replay(ev, LIM))
    assert s == want and head.split()[1] == str(len(s)) and head.split()[2] == f"{mk.fnv1a(s):016x}"
    assert set(counts) == set("." + rg.CODES)                       # every check refuses something
    assert ev == mk.events()                                         # the fixture is current


@pytest.mark.parametrize("field,at,past,code", [("collar", 1_020_000, 1_020_001, "C"), ("qty", 2_000, 2_001, "Q")])
def test_boundaries(field, at, past, code):
    g = gate()
    args = (lambda v: ("B", 100, v)) if field == "collar" else (lambda v: ("B", v, 1_000_000))
    assert g.check(1, "S1", 1, *args(at), 1)[0] == "."
    assert g.check(2, "S1", 1, *args(past), 2)[0] == code


def test_position_counts_orders_in_flight_and_frees_them_when_done():
    g = gate()
    for k in range(2):                                   # max_long 5,000 on instrument 1, max_qty 2,000
        assert g.check(10 + k, "S1", 1, "B", 2_000, 1_000_000 - 100 * k, 10 + k)[0] == "."
    assert g.check(20, "S1", 1, "B", 1_001, 1_000_000, 20)[0] == "L"   # 4,000 in flight + 1,001
    assert g.check(21, "S1", 1, "B", 1_000, 999_800, 21)[0] == "."     # exactly 5,000
    g.on_fill(10, 2_000, 1_000_000)
    g.on_done(11)                                        # cancelled: its 2,000 leave the exposure
    assert g.pos[1] == 2_000 and g.open_buy[1] == 1_000
    assert g.check(30, "S1", 1, "B", 2_000, 999_700, 30)[0] == "."     # 2,000 + 1,000 + 2,000 = 5,000


def test_fail_closed():
    g = gate()
    assert g.check(LIM[1].max_age_ns + 1, "S1", 1, "B", 100, 1_000_000, 1)[0] == "S"
    g.heartbeat(LIM[1].max_age_ns + 1)
    assert g.check(LIM[1].max_age_ns + 2, "S1", 1, "B", 100, 1_000_000, 2)[0] == "R"  # the reference is stale too
    assert rg.Gate(LIM[1], 0).check(1, "S1", 2, "B", 100, 250_000, 3)[0] == "R"         # no reference at all


def test_kill_switch_levels_and_actions():
    g = gate()
    g.set_reference(0, 2, 250_000)
    for cl, s in ((1, "S1"), (2, "S2"), (3, "S3")):
        assert g.check(cl, s, 1, "B", 100, 1_000_000, cl)[0] == "."
    g.on_fill(1, 100, 1_000_000)
    assert g.kill(10, "desk", "D1", "cancel") == [2]     # order 1 is done; S3 is on desk D2
    assert g.check(11, "S1", 1, "B", 100, 1_000_000, 4)[0] == "K"
    assert g.check(12, "S3", 1, "B", 100, 999_900, 5)[0] == "."
    # order 2 stays open until the venue confirms its cancel: it is cancelled again, with the rest
    assert g.kill(13, "firm", "", "flatten") == [2, 3, 5, (1, "S", 100, 1_000_000)]
    g.unkill("firm")
    g.unkill("desk", "D1")
    assert g.check(14, "S1", 1, "B", 100, 999_800, 6)[0] == "."


def test_limits_change_between_events_only_and_throttle_refills():
    g = gate()
    for k in range(20):                                   # S1: burst 20, rate 2,000 a second
        assert g.check(1_000 + k, "S1", 1, "B" if k % 2 else "S", 100, 1_000_000 - 100 * k, 1_000 + k)[0] in ".O"
    g2 = rg.Gate(LIM[1], 0)
    g2.set_reference(0, 3, 1_500_000)
    codes = [g2.check(10 + k, "S2", 3, "B", 100, 1_500_000 - 100 * k, 100 + k)[0] for k in range(6)]
    assert codes == [".", ".", ".", ".", ".", "T"]        # S2: burst 5
    assert g2.check(10 + 2_000_000, "S2", 3, "B", 100, 1_400_000 + 100, 200)[0] == "."   # 2 ms at 500/s: one token
    g2.set_limits(20, LIM[2])
    assert g2.lim.version == 2


def test_random_streams_keep_the_books_consistent():
    rng = random.Random(3)
    for seed in range(5):
        ev = mk.events(seed=seed, n=2_000)
        g = rg.replay(ev, LIM)
        # rebuild the open exposure from the orders still open: the running sums must match it exactly
        ob, os_ = {}, {}
        for o in g.orders.values():
            d = ob if o.side == "B" else os_
            d[o.instr] = d.get(o.instr, 0) + o.qty - o.filled
        assert {k: v for k, v in g.open_buy.items() if v} == {k: v for k, v in ob.items() if v}
        assert {k: v for k, v in g.open_sell.items() if v} == {k: v for k, v in os_.items() if v}
        assert all(st.open == sum(1 for o in g.orders.values() if o.strat == s) for s, st in g.strat.items())
        assert rng.random() >= 0


def test_riskctl_adapter():
    d = json.loads((HERE / "data/limits.json").read_text())["1"]
    assert rg.from_riskctl(d) == rg.Limits.from_dict(d) == rg.from_riskctl({"riskgate": d})
    fixture = HERE.parent / "riskctl/data/limits.json"
    if not fixture.exists():
        pytest.skip("Book 11's firm.riskctl has not landed")
    lim = rg.from_riskctl(json.loads(fixture.read_text()))      # Book 11's policy, exported for this gate
    assert lim.version == 1 and set(lim.strategies) == {"etf_arb", "quoter_a", "quoter_b"}
    g = rg.Gate(lim, 0)
    g.set_reference(0, 1, 1_000_000)
    assert g.check(1, "quoter_a", 1, "B", 5_000, 1_000_000, 1)[0] == "."   # at the instrument's max_qty
    assert g.check(2, "quoter_a", 1, "B", 5_001, 1_000_000, 2)[0] == "Q"
    assert g.check(3, "quoter_a", 1, "B", 100, 1_060_000, 3)[0] == "C"     # outside the 500 bp collar


def test_runaway_is_stopped_by_the_right_checks():
    res = {k: ra.run(c, 2.0) for k, c in ra.CONFIGS.items()}
    assert res["none"].sent == 3_000 and res["none"].position == 300_000
    assert res["collar"].sent == res["none"].sent                     # the price follows the runaway: no trip
    assert res["size and notional"].sent == res["none"].sent          # small child orders: no trip
    assert 0 < res["throttle"].last_second <= 500                      # slowed, not stopped
    assert res["position (in flight)"].position == 20_000 and res["position (in flight)"].last_second == 0
    assert res["position (fills only)"].position > 20_000              # overshoots by the orders in flight
    assert res["capital threshold"].last_second == 0
    assert res["position + kill switch"].killed
