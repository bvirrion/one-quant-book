import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from wrappers import WRAPPERS, DrTerms, breakdown, crossover_years, dr_band_bp, parity, total

W = {w.name: w for w in WRAPPERS}


def test_breakdown_adds_up_and_cash_investor_pays_no_funding_on_shares():
    b = breakdown(W["shares"], 1.0, 200.0, 0.0)
    assert b == {"trading": 10.0, "tax": 50.0, "running": 0.0, "funding": 0.0, "dividends": 30.0}
    assert total(W["shares"], 1.0, 200.0, 1.0) == pytest.approx(140.0)
    assert breakdown(W["future"], 1.0, 200.0, 0.0)["funding"] == 30.0          # inside the price


def test_crossover_between_shares_and_swap():
    # leveraged: shares 60 fixed + 80/yr, swap 6 fixed + 50/yr -> the swap always wins
    assert crossover_years(W["shares"], W["swap"], 200.0, 1.0) is None
    # unleveraged: shares 60 fixed + 30/yr, swap 6 fixed + 50/yr -> shares win after 2.7 years
    assert crossover_years(W["shares"], W["swap"], 200.0, 0.0) == pytest.approx(2.7)


def test_receipt_band_is_asymmetric_with_an_entry_tax():
    t = DrTerms(4.0, 0.05, 0.05, 150.0, 6.0)
    assert parity(5.0, 1.25, t) == pytest.approx(25.0)
    lo, hi = dr_band_bp(5.0, 1.25, t)
    assert lo == pytest.approx(-26.0) and hi == pytest.approx(176.0)
