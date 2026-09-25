import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_sphedge import BOOK, MarketState, Note, book_exposures, note_value, recycling_impact  # noqa: E402


def test_signs_of_the_issuer_book():
    e = book_exposures(paths=4000)
    assert e["vega"]["total"] > 0 and e["skew"]["total"] > 0 and e["dividends"]["total"] > 0
    assert e["correlation"]["total"] < 0 and set(e["correlation"]["by_note"]) == {BOOK[2].name}


def test_note_values_are_sensible():
    single = Note("x", 1e8, (0,), 7.0)
    v = note_value(single, MarketState(), 4000)
    assert 90 < v < 110 and note_value(single, MarketState(), 4000, spot=0.3) < 50


def test_worst_of_gains_from_correlation():
    worst = Note("y", 1e8, (0, 1), 9.0)
    assert note_value(worst, MarketState(corr=0.95), 4000) > note_value(worst, MarketState(corr=0.3), 4000)


def test_recycling_by_hand():
    r = recycling_impact(10e6, 5e6)
    assert r["move"] == -2.0 and r["seller_cost"] == 10e6 and r["buyer_gain"] == 20e6
