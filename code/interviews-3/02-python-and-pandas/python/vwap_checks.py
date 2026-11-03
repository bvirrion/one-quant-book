import math

import pandas as pd
import pytest
from iv_vwap import vwap_by_symbol_day


def table(*rows):
    return pd.DataFrame(rows, columns=["symbol", "day", "price", "qty"])


@pytest.mark.parametrize("rows, want", [
    ([("A", 1, 10.0, 100)], 10.0),                       # one trade
    ([("A", 1, 10.0, 100), ("A", 1, 11.0, 300)], 10.75), # weighted, not 10.5
    ([("A", 1, 0.1, 1), ("A", 1, 0.2, 1)], 0.15),        # needs approx
])
def test_one_group(rows, want):
    got = vwap_by_symbol_day(table(*rows))
    assert got.loc[("A", 1)] == pytest.approx(want)


def test_zero_quantity_is_not_a_number():
    assert math.isnan(vwap_by_symbol_day(table(("A", 1, 10.0, 0))).loc[("A", 1)])
