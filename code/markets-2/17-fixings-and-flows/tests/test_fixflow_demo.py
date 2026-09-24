"""Chapter 17 of Book 2: the fixing order and flows behave as the text says."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from fixflow_demo import fixing_order, price_path


def test_path_ends_at_total_impact():
    for p in (0.0, 0.5, 1.0):
        path = price_path(p)
        assert abs(path[-1][1] - 3.0) < 1e-9 and path[0][1] == 0.0


def test_profit_grows_with_prehedge():
    pnls = [fixing_order(p / 10)["pnl"] for p in range(11)]
    assert pnls == sorted(pnls) and pnls[0] == 0.0
