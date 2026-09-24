"""Numbers gate: every numerical answer printed in the Chapter 9 text and solutions."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from stale_tape import VENUE_DELAYS_US, Market, sniping_profit_ticks, stale_fraction

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/nbbo"))
from firm_nbbo import NbboBuilder, Quote


def test_text():
    b = NbboBuilder()
    for v, q in (("X", (100_000, 300, 100_200, 500)), ("Y", (100_100, 200, 100_200, 100)),
                 ("Z", (100_100, 400, 100_300, 900))):
        b.update(Quote(v, *q))
    n = b.nbbo()
    assert (n.bid, n.bid_size, n.ask, n.ask_size) == (100_100, 600, 100_200, 600)
    assert b.trades_through(+1, 100_300)
    assert round(stale_fraction(Market(), 1000.0) * 100, 2) == 0.51
    assert round(stale_fraction(Market(jumps_per_second=50.0), 1000.0) * 100, 1) == 4.9
    assert sniping_profit_ticks(Market()) == 3636
    assert round(0.20 + 0.18, 2) == 0.38
    assert round(50.6 * 0.813, 1) == 41.1 and round(50.6 * 0.187, 1) == 9.5
    assert 50 * 3000 == 150_000


def test_exercises():
    b = NbboBuilder()
    for v, q in (("A", (251_000, 500, 251_400, 200)), ("B", (251_100, 100, 251_300, 300)),
                 ("C", (251_100, 300, 251_300, 50)), ("D", (251_200, 80, 251_500, 400))):
        b.update(Quote(v, *q))
    n = b.nbbo()                                                                   # 1
    assert (n.bid, n.bid_size, n.bid_venues) == (251_100, 400, ("B", "C"))
    assert (n.ask, n.ask_size, n.ask_venues) == (251_300, 300, ("B",))
    assert [48 * 100, 251 * 40, 999 * 40, 4200 * 10, 712_000] == [4800, 10_040, 39_960, 42_000, 712_000]   # 2
    adv = 17.6e9                                                                   # 3
    assert [round(x / 1e9, 1) for x in (adv * 0.494, adv * 0.506 * 0.813, adv * 0.506 * 0.187)] == [8.7, 7.2, 1.7]
    assert 1.1e12 / adv == pytest.approx(62.5)
    assert round(0.30 - 0.25, 2) == 0.05 and round(0.14 - 0.10, 2) == 0.04 and round(0.25 + 0.14, 2) == 0.39   # 5
    assert 12 * 600e-6 == pytest.approx(0.0072) and round(0.0072 * 23_400) == 168                            # 6
    half = Market(venue_delays_us=tuple(d / 2 for d in VENUE_DELAYS_US))                                      # 7
    assert round(stale_fraction(Market(), 500.0) * 100, 3) == round(stale_fraction(half, 500.0) * 100, 3) == 0.255


def test_problem():
    lam, day = 8 / 60, 23_400
    assert round(lam * 900e-6 * 100, 3) == 0.012 and round(lam * 900e-6 * day, 1) == 2.8
    ep = 0.65 * 0 + 0.25 * 1 + 0.10 * 2
    assert ep == pytest.approx(0.45)
    jumps = lam * day
    assert jumps == pytest.approx(3120)
    assert ep * 4 * 3 == pytest.approx(5.40) and ep * 4 * 3 * jumps == pytest.approx(16_848)
    ep_fee = 0.25 * (1 - 0.30) + 0.10 * (2 - 0.30)
    assert ep_fee == pytest.approx(0.345) and round(ep_fee * 4 * 3 * jumps) == 12_917
    loss = ep * 3 * jumps
    assert loss == pytest.approx(4212) and round(loss / 400_000 * 100, 2) == 1.05
    assert round(0.35 - loss / 400_000 * 100, 2) == -0.70 and round(loss * 252 / 1e6, 2) == 1.06
    assert 0.25 * 0.9 + 0.10 * 1.9 == pytest.approx(0.415)
