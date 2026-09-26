import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "exchsim"))
from firm_exchsim import SEC, ExchangeConfig, Order, Phases, Simulator  # noqa: E402
from firm_halts import LULD, Combined, MarketWide, Velocity  # noqa: E402

T0 = 34_200 * SEC


def _run(policy, orders, seconds=60):
    end = T0 + seconds * SEC
    cfg = ExchangeConfig(phases=Phases(start_ns=T0 - SEC, open_ns=T0, close_ns=end, end_ns=end + 1), halts=policy)
    sim = Simulator(cfg, seed=1)
    sim.add_events(orders=[(T0 + int(t * SEC), "SIMX", o) for t, o in orders])
    return sim.run()


def book(px=1_000_000, lots=5):
    out = []
    for k in range(1, 30):
        out += [(0.1, Order(side="B", qty=100 * lots, price=px - 100 * k)),
                (0.1, Order(side="S", qty=100 * lots, price=px + 100 * k))]
    return out


def test_band_holds_and_limit_state_pauses():
    pol = LULD(0.001, window_s=10, limit_state_s=2, pause_s=5, update_pct=0.001)   # the sweep does not move it
    # a trade at 100.00 sets the reference; a large sell sweeps the bids down to the band (99.90) and stops there;
    # an offer at the band is a limit state, which lasts and pauses the stock
    orders = book() + [(1.0, Order(side="B", qty=100, price=1_000_100)), (1.2, Order(side="S", qty=100, price=999_900))]
    orders += [(3.0, Order(side="S", qty=100 * 100, price=0, tif="I")), (3.1, Order(side="S", qty=100, price=999_000))]
    res = _run(pol, orders)
    lo = pol.bands[0][1]
    assert lo == 999_000 and pol.bands[0][2] == 1_001_000
    assert min(p for _, _, p, *_ in res.engine().trades) >= lo       # nothing printed below the band (bids placed
    #                                                                     below it were rejected at entry)
    events = [e[1] for e in pol.log]
    assert events[:3] == ["limit", "pause", "resume"]
    assert pol.log[2][0] - pol.log[1][0] >= 5.0 - 1e-9 and pol.log[1][0] - pol.log[0][0] >= 2.0 - 1e-9


def test_market_wide_and_velocity():
    mw = MarketWide(levels=(0.001,), halt_s=5, reference=1_000_000)
    orders = book() + [(2.0, Order(side="S", qty=100 * 100, price=0, tif="I"))]
    _run(mw, orders, 30)
    assert [e[1] for e in mw.log] == ["halt", "resume"]
    ve = Velocity(3, window_s=1.0, pause_s=2.0)
    _run(Combined(ve), book() + [(2.0, Order(side="S", qty=100 * 5 * 5, price=0, tif="I"))], 30)
    assert [e[1] for e in ve.log][:2] == ["pause", "resume"]
