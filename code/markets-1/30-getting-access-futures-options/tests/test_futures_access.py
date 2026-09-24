import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from futures_access import ES, MICRO, breakevens, exchange_round_trip_in_ticks


def test_breakevens():
    lease, own = breakevens()
    assert lease == pytest.approx(1_500 / 0.88) and own == pytest.approx(2_500 / 0.12)


def test_the_small_contract_is_expensive_in_ticks():
    e, m = exchange_round_trip_in_ticks(ES, 12.5), exchange_round_trip_in_ticks(MICRO, 1.25)
    assert m["non_member"] > e["non_member"] and m["non_member"] == pytest.approx(0.352)
