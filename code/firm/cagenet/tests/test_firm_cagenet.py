import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_cagenet as cg  # noqa: E402

D, C = cg.Device, cg.Cable


def chain(kind, fabric):
    return cg.Cage([D("h", "handoff"), D("x", kind, fabric), D("s", "server")], [C("h", "x", 10.0), C("x", "s", 10.0)])


def test_latency_by_device_kind():
    prop = 2 * 10.0 * 1.462 / 299_792_458 * 1e9
    ser = 8 * 100 / 10
    for kind, fabric, add in (("l1", 4, 4), ("mux", 39, 39), ("cut-through", 250, 250 + 51.2),
                              ("store-and-forward", 500, 500 + 80)):
        c = chain(kind, fabric)
        p = c.path("h", "s")
        assert p == ["h", "x", "s"]
        assert c.latency_ns(p, 100, 10.0) == pytest.approx(ser + prop + add)
    tap = chain("tap", 0)
    assert tap.latency_ns(["h", "x", "s"], 100, 10.0) == pytest.approx(ser + prop)


def test_paths_do_not_cross_servers_or_handoffs():
    c = cg.Cage([D("a", "handoff"), D("s1", "server"), D("s2", "server")], [C("a", "s1", 1), C("s1", "s2", 1)])
    assert c.path("a", "s2") is None and c.path("a", "s1") == ["a", "s1"]


def test_single_points_and_taps():
    dev = [D("A", "handoff"), D("B", "handoff"), D("O", "handoff"), D("sw", "cut-through", 250),
           D("tapA", "tap"), D("s", "server")]
    cab = [C("A", "tapA", 1), C("tapA", "sw", 1), C("B", "sw", 1), C("O", "sw", 1), C("sw", "s", 1)]
    c = cg.Cage(dev, cab)
    names = {e if isinstance(e, str) else (e.a, e.b) for e in c.single_points(["A", "B"], ["O"], ["s"])}
    assert "sw" in names and ("sw", "s") in names and "tapA" not in names      # line B still feeds s without tapA
    assert c.untapped(["A", "B", "O"]) == ["B", "O"]
    with pytest.raises(ValueError):
        cg.Cage([D("x", "router")], [])
