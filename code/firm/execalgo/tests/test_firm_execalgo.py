import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
for c in ("agentmkt", "exchsim"):
    sys.path.insert(0, str(HERE.parent / c))
from firm_agentmkt import T0, ZERO, MarketMaker, Population, PopulationConfig  # noqa: E402
from firm_exchsim import CTL, SEC, ExchangeConfig, LatencyModel, Phases, SessionSpec, Simulator  # noqa: E402
from firm_execalgo import ISAlgo, Params, shortfall_bp  # noqa: E402

MK = PopulationConfig(lo_rate=3.0, near=0.5, cancel=0.02, depth=10, noise=1.2, fund=0.2, v_rate=0.1, run_tail=2.5)


def go(algo, seconds=300.0, seed=4, controls=(), calls=()):
    end = T0 + int(seconds * SEC)
    sim = Simulator(ExchangeConfig(phases=Phases(start_ns=T0 - SEC, open_ns=T0, close_ns=end, end_ns=end + 1)), seed=seed)
    sim.add_agent(Population(MK, seed, seconds), SessionSpec(firm="POP", latency=ZERO, cod=False))
    for a in (MarketMaker(skew=0.1), algo):
        sim.add_agent(a, SessionSpec(firm=a.name.upper(), latency=LatencyModel(20_000, 20_000, 20_000)))
    sim.add_events(controls=[(T0 + int(t * SEC), "", m) for t, m in controls])
    for t, fn in calls:
        sim.schedule_call(T0 + int(t * SEC), fn)
    return sim.run()


def test_algorithm_completes_within_its_band_and_twap_crosses_only():
    a = ISAlgo(Params(qty=3000, start_s=20, horizon_s=200, urgency=2.0))
    go(a)
    assert a.state == "done" and a.filled == 3000 and a.log[0][2] == "start" and a.log[-1][2] == "done"
    early = sum(q for t, _, q in a.fills if t < 100)
    assert early > 1500                                            # urgency front-loads the schedule
    tw = ISAlgo(Params(qty=3000, start_s=20, horizon_s=200, urgency=0.0, passive=False, band=(0, 1), check_s=10,
                       tol_s=0), name="twap")
    res = go(tw)
    assert tw.filled == 3000 and all(f[6] == "R" for f in res.agents["twap"].fills)   # takes liquidity only


def test_halt_pauses_and_shifts_the_schedule():
    a = ISAlgo(Params(qty=3000, start_s=20, horizon_s=200))
    go(a, controls=[(100.0, CTL["P"](1, "H", "NEWS")), (130.0, CTL["P"](1, "U", "RESM")),
                    (130.000001, CTL["P"](1, "T", "RESM"))])
    ev = [e for _, _, e, _ in a.log]
    assert ev[:3] == ["start", "pause", "resume"] and a.paused_s > 29 and a.state == "done"
    assert not [t for t, _, _ in a.fills if 80.001 < t < 110]      # nothing traded while halted


def test_limit_collar_and_kill():
    probe = ISAlgo(Params(qty=100, start_s=5, horizon_s=10), name="probe")
    go(probe, seconds=30)
    lim = int(probe.arrival)                                       # a buy limit at the arrival mid
    a = ISAlgo(Params(qty=3000, start_s=5, horizon_s=200, limit=lim))
    go(a, seconds=260)
    assert all(px <= lim for _, px, _ in a.fills)
    c = ISAlgo(Params(qty=3000, start_s=20, horizon_s=200, collar_ticks=0, passive=False))
    go(c)
    assert c.filled == 0 and any(e == "reject" for _, _, e, _ in c.log)
    k = ISAlgo(Params(qty=3000, start_s=20, horizon_s=200))
    go(k, calls=[(120.0, k.kill)])
    assert k.state == "killed" and k.filled < 3000 and k.log[-1][2] == "kill"


def test_shortfall_arithmetic():
    fills = [(0, 1_000_100, 100), (1, 1_000_300, 100)]
    assert abs(shortfall_bp("B", fills, 1_000_000, 200, 1_000_000) - 2.0) < 1e-12
    assert abs(shortfall_bp("B", fills[:1], 1_000_000, 200, 1_000_500) - 3.0) < 1e-12   # half unfilled, price up 5 bp


def test_crossing_sweeps_the_venues_displayed_quotes():
    from firm_exchsim import Order
    ph = Phases(start_ns=T0 - SEC, open_ns=T0, close_ns=T0 + 30 * SEC, end_ns=T0 + 30 * SEC + 1)
    sim = Simulator([ExchangeConfig(venue=n, phases=ph) for n in ("A", "B")], seed=1)
    ev = []
    for n, q in (("A", 300), ("B", 500)):
        ev += [(T0 + SEC // 10, n, Order(side="S", qty=q, price=1_000_100)),
               (T0 + SEC // 10, n, Order(side="B", qty=1000, price=999_900))]
    sim.add_events(orders=ev)
    a = ISAlgo(Params(qty=800, start_s=1, horizon_s=5, urgency=0.0, passive=False, band=(0, 1), tol_s=0),
               venues=["A", "B"])
    sim.add_agent(a, [SessionSpec(venue=n, firm="ALGO", latency=LatencyModel(20_000, 20_000, 20_000)) for n in "AB"])
    res = sim.run()
    by = {}
    for f in res.agents["algo"].fills:
        by[f[1]] = by.get(f[1], 0) + f[5]
    assert a.filled == 800 and by == {0: 300, 1: 500} and a.state == "done"


def test_i_would_price_trades_ahead_of_schedule_up_to_the_band():
    probe = ISAlgo(Params(qty=100, start_s=5, horizon_s=10), name="probe")
    go(probe, seconds=30)
    slow = ISAlgo(Params(qty=6000, start_s=20, horizon_s=250, urgency=0.0, band=(0.0, 0.2)))
    go(slow)
    eager = ISAlgo(Params(qty=6000, start_s=20, horizon_s=250, urgency=0.0, band=(0.0, 0.2),
                          i_would=int(probe.arrival) + 10_000))            # a buyer happy to pay a dollar more
    go(eager)
    early = [sum(q for t, _, q in a.fills if t < 60) for a in (slow, eager)]
    assert early[1] > early[0] and any(e == "i-would" for _, _, e, _ in eager.log)
