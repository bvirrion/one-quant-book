import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_docterms as dt  # noqa: E402


def test_call_threshold_mta_rounding_haircut():
    a = dt.Annex(threshold=10.0, mta=1.0, rounding=0.5, independent_amount=2.0, haircuts={"cash": 0.0, "bond": 0.1})
    assert dt.held_value(a, {"cash": 3.0, "bond": 10.0}) == 12.0
    assert dt.call(a, 30.0, {"cash": 3.0, "bond": 10.0}) == 10.0          # 30 + 2 - 10 - 12 = 10
    assert dt.call(a, 20.6, {"cash": 3.0}) == 10.0                           # 9.6 rounded up
    assert dt.call(a, 10.0, {"cash": 3.0}) == -1.0 and dt.call(a, 10.5, {"cash": 3.0}) == 0.0 and dt.call(a, 5.0, {"cash": 3.0}) == -3.0
    assert dt.held_value(a, {"equity": 5.0}) == 0.0                           # ineligible: full haircut


def test_triggers():
    t = dt.Trigger("pb", ((2, 0.2),), floor=50.0)
    assert dt.first_trip([100, 95, 79, 60], t) == (2, "fall of 20% over 2 days")
    assert dt.first_trip([100, 49], t) == (1, "below floor 50")


def test_close_out():
    x = dt.close_out({"swaps": 10.0, "repo": -4.0}, {"swaps": 3.0}, True)
    assert x["balances"] == {"swaps": 7.0, "repo": -4.0} and x["net"] == 3.0
    assert dt.close_out({"swaps": 10.0}, {}, False)["net"] is None
