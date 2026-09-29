"""The design in Verilator and Icarus, the Python cycle model and the fixture's expectations must agree order for order
and cycle for cycle; the message-level reference must see the same triggers. Fails if a simulator is missing."""
import functools
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_hwtrade as hw  # noqa: E402
import make_hwtrade_fixture as mf  # noqa: E402


@functools.lru_cache
def fixture():
    pk = mf.load()
    return pk, hw.beats_of(pk)


def expected():
    rows = [r.split() for r in (HERE / "data" / "expected.txt").read_text().splitlines() if not r.startswith("#")]
    return [tuple(int(x) for x in r) for r in rows]


def digest(orders):
    return sum((i + 1) * (c * 7 + q * 13 + p) for i, (c, _, q, p) in enumerate(orders)) % (1 << 61)


@pytest.fixture(scope="module")
def sims(tmp_path_factory):
    d = tmp_path_factory.mktemp("hwt")
    hw.write_stim(d / "stim.txt", fixture()[1])
    return d, hw.build_verilator(d / "v", {}), hw.build_icarus(d, {})


def test_python_model_matches_fixture():
    pk, beats = fixture()
    for thresh, maxq, kill, n, rej, first, dg in expected():
        orders, rejects = hw.CycleModel().run(beats, thresh, maxq, kill)
        assert (len(orders), rejects, orders[0][0], digest(orders)) == (n, rej, first, dg)
        if kill < 0 and maxq >= 10_000:
            assert len(orders) + rejects == len(hw.triggers(pk, thresh))          # every trigger decided once


def test_hdl_in_both_simulators(sims):
    d, v, i = sims
    beats = fixture()[1]
    for thresh, maxq, kill, *_ in expected():
        a = hw.run_verilator(v, d / "stim.txt", thresh, maxq, kill)
        b = hw.run_icarus(i, d / "stim.txt", thresh, maxq, kill)
        assert a == b and hw.parse_output(a) == hw.CycleModel().run(beats, thresh, maxq, kill)


def test_risk_boundaries_and_kill():
    pk, beats = fixture()
    base, _ = hw.CycleModel().run(beats, 1_000_300, 10_000)
    sizes = sorted({q for _, _, q, _ in base})
    cap = sizes[len(sizes) // 2]
    orders, _ = hw.CycleModel().run(beats, 1_000_300, cap)
    assert orders and max(q for _, _, q, _ in orders) == cap                  # at the limit passes, above does not
    kill_at = base[10][0] - 1
    killed, _ = hw.CycleModel().run(beats, 1_000_300, 10_000, kill_at)
    assert all(c < kill_at for c, *_ in killed) and len(killed) == 10        # nothing leaves once kill is set
    burst, _ = hw.CycleModel(burst=1, refill=10_000).run(beats, 1_000_300, 10_000)
    assert len(burst) == 1 + (len(beats) + 8) // 10_000                        # the bucket rations


def test_decision_takes_two_edges_after_the_price():
    """A single packet with one qualifying add order: the order appears two cycles after the beat with the price."""
    msg = b"A" + (1).to_bytes(2, "big") + bytes(16) + b"S" + (700).to_bytes(4, "big") + b"STOCK   " + (1_000_100).to_bytes(4, "big")
    pkt = b"SESSION001" + (1).to_bytes(8, "big") + (1).to_bytes(2, "big") + (36).to_bytes(2, "big") + msg
    beats = hw.beats_of([pkt])
    orders, _ = hw.CycleModel().run(beats, 1_000_200, 10_000)
    price_end = 20 + 2 + 35                                                    # byte index of the price's last byte
    assert orders == [(price_end // 8 + 2, 1, 700, 1_000_100)]
    assert hw.wirepath_stage(3, 156.25).p50_ns == pytest.approx(19.2)
