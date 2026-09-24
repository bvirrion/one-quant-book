"""Numbers gate: every numerical answer printed in Book 3, Chapter 14 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/gasfee"))
from firm_gasfee import GWEI, confirmation_seconds, next_base_fee, tx_cost_usd
from m3_chain import LIMIT, arbitrage_breakeven, demand_shock, full_blocks

A = arbitrage_breakeven()


def test_text():
    assert round(full_blocks(20), 2) == 105.45 and round(full_blocks(20) / 10, 1) == 10.5
    assert round(tx_cost_usd(150_000, full_blocks(20), 2, 3000), 2) == 48.35 and round(A["cost_now"], 2) == 5.40
    assert round(2 * 32 * 12 / 60, 1) == 12.8


def test_exercises():
    assert next_base_fee(20 * GWEI, int(0.75 * LIMIT), LIMIT) == 21.25 * GWEI
    assert confirmation_seconds("bitcoin") == 3600 and confirmation_seconds("ethereum") == 768
    assert round(math.log(2) / math.log(1.125), 1) == 5.9 and round(1.125**6, 2) == 2.03
    assert round(math.log(0.5) / math.log(0.875), 1) == 5.2 and round(0.875**5 * 100) == 51 and round(0.875**6 * 100) == 45
    assert round(tx_cost_usd(150_000, 30, 2, 3000), 2) == 14.40
    d = demand_shock()
    assert round(max(b for _, b, _ in d), 2) == 39.20 and [n for n, _, s in d if n >= 5 and s < 1][0] == 11


def test_problem():
    assert full_blocks(1) == 11.25 and 20 * 12 == 240
    assert round(A["breakeven_gwei"], 2) == 131.33 and math.ceil(A["blocks"]) == 22 and round(A["blocks"], 1) == 21.9
    a2 = arbitrage_breakeven(120)
    assert round(a2["breakeven_gwei"], 2) == 264.67 and math.ceil(a2["blocks"]) == 28
