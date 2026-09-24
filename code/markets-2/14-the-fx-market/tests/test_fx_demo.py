"""Chapter 14 of Book 2: the demo's crosses, dates and survey data behave as the text says."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from fx_demo import LEGS, crosses, load_bis, relative_spread_bp


def test_relative_spreads_add():
    c = crosses()
    for pair, (a, b) in {"EURJPY": ("EURUSD", "USDJPY"), "GBPJPY": ("GBPUSD", "USDJPY")}.items():
        assert math.isclose(relative_spread_bp(c[pair]), relative_spread_bp(LEGS[a]) + relative_spread_bp(LEGS[b]),
                            rel_tol=1e-3)


def test_bis_shares():
    rows = load_bis()
    inst = [r for r in rows if r["series"] == "instrument"]
    assert abs(sum(float(r["y2025"]) for r in inst) - 101) <= 1 and abs(sum(float(r["y2022"]) for r in inst) - 100) <= 1
    usd = next(r for r in rows if r["label"] == "USD")
    assert float(usd["y2025"]) == 89.2
