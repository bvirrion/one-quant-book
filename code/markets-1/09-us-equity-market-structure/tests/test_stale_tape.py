import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from stale_tape import Market, net_price, sniping_profit_ticks, stale_fraction


def test_a_tape_with_no_delay_is_never_stale():
    assert stale_fraction(Market(), 0.0) == 0.0


def test_staleness_is_about_jump_rate_times_delay():
    m = Market()
    assert stale_fraction(m, 1000.0) == pytest.approx(m.jumps_per_second * 1000e-6, rel=0.25)
    assert stale_fraction(m, 2000.0) > stale_fraction(m, 500.0)


def test_sniping_profit_counts_only_big_jumps():
    assert sniping_profit_ticks(Market(seconds=600.0)) > 0
    assert sniping_profit_ticks(Market(venue_delays_us=(50.0,))) == 0.0


def test_net_price():
    assert net_price(10.00, +1, 0.0030) == pytest.approx(10.0030)
    assert net_price(10.00, +1, -0.0015) == pytest.approx(9.9985)
