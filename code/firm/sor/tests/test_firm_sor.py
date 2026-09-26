import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "exchsim"))
from firm_sor import (  # noqa: E402
    Fader,
    Router,
    Venue,
    VenueStats,
    child_sizes,
    ck_allocate,
    ck_cost,
    dark_first,
    send_delays,
    sweep,
)

V = [Venue("A", 50_000), Venue("B", 150_000)]


def test_delays_sweep_and_ranking():
    assert send_delays(V, False) == {"A": 0, "B": 0}
    assert send_delays(V, True) == {"A": 100_000, "B": 0} and send_delays(V, True, 5)["B"] == 5
    legs = sweep([("A", 101, 300), ("B", 100, 200), ("C", 100, 500)], 600, {"A": 0.003, "B": 0.003, "C": -0.001})
    assert legs == [("C", 100, 500), ("B", 100, 100)]
    s = VenueStats()
    s.add("A", 100, 100)
    s.add("B", 100, 40)
    assert s.fill_ratio("B", (0, 0)) == 0.4
    assert [v for v, _ in s.rank(["A", "B"], {"A": 0.003, "B": -0.001})] == ["A", "B"]


def _run(sync):
    from firm_exchsim import SEC, ExchangeConfig, LatencyModel, Order, Phases, SessionSpec, Simulator
    t0 = 34_200 * SEC
    ph = Phases(start_ns=t0 - SEC, open_ns=t0, close_ns=t0 + SEC, end_ns=t0 + SEC + 1)
    sim = Simulator([ExchangeConfig(venue=n, phases=ph) for n in ("A", "B")], seed=3)
    sim.add_events(orders=[(t0 + 1000, n, Order(side="S", qty=q, price=p)) for n in ("A", "B")
                           for q, p in ((100, 1_000_100), (500, 1_000_200))])
    sim.add_agent(Fader(1_000_100, 200, ["A", "B"], t0 + 2000),
                  [SessionSpec(venue=n, firm="HFT", cod=False, latency=LatencyModel(m, m, m))
                   for n, m in (("A", 5_000), ("B", 40_000))])
    r = Router([("A", 1_000_100, 300), ("B", 1_000_100, 300)], V, t0 + 10_000_000, sync, cleanup={"A": 500, "B": 500})
    sim.add_agent(r, [SessionSpec(venue=v.name, firm="RTR", latency=LatencyModel(v.entry_ns, v.entry_ns, v.entry_ns))
                      for v in V])
    sim.run()
    return r


def test_fader_and_synchronised_sweep():
    spray, sync = _run(False), _run(True)
    assert spray.first_filled == 400 and sync.first_filled == 600      # B's fast 200 faded before the spray arrived
    assert sum(spray.filled_by_venue.values()) == 600                   # the clean-up took the rest a tick higher


def test_cont_kukanov():
    xi = np.array([[500.0, 100.0], [300.0, 400.0], [800.0, 0.0]])
    c, got = ck_cost(0.0, [200.0, 100.0], 300, [100.0, 50.0], xi, 0.005, 0.003, [0.002, 0.0], 0.02, 0.02)
    assert np.allclose(got, [250.0, 300.0, 200.0])
    assert np.isclose(c[1], -0.007 * 200 - 0.005 * 100)
    rng = np.random.default_rng(0)
    xi = np.exp(rng.normal(np.log([900.0, 600.0]), 0.5, (300, 2)))
    args = (1000, [400.0, 100.0], xi, 0.005, 0.003, [0.002, 0.001], 0.012, 0.012)
    m, lim = ck_allocate(*args)
    best = ck_cost(m, lim, *args[:1], *args[1:])[0].mean()
    for alt in ((1000.0, [0.0, 0.0]), (0.0, [500.0, 500.0]), (0.0, [1000.0, 0.0])):
        assert best <= ck_cost(alt[0], alt[1], *args[:1], *args[1:])[0].mean() + 1e-9


def test_anti_gaming():
    rng = np.random.default_rng(4)
    s = child_sizes(5000, 7, rng)
    assert sum(s) == 5000 and all(x % 100 == 0 for x in s) and len(set(s)) > 1
    assert dark_first(1000, ["D1", "D2"], 300) == [("D1", 1000, 300), ("D2", 1000, 300)]
