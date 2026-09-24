"""Tests of the Chapter 14 teaching module (Book 3): the demand shock is stable to its own settings."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from m3_chain import demand_shock


def test_base_fee_converges_to_demand():
    d = demand_shock(blocks=200, start=5, end=180)
    assert abs(d[179][1] - 40.0) < 0.5                    # four times the demand -> four times the base fee
    assert d[4][2] == 0.5 and d[5][2] == 1.0
