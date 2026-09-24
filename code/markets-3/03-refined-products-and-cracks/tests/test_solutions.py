"""Numbers gate: every numerical answer printed in Book 3, Chapter 3 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/cracks"))
from firm_cracks import (
    arbitrage_open,
    barrels_per_tonne,
    gross_refining_margin,
    hedge_lots,
    per_gallon_to_per_barrel,
    per_tonne_to_per_barrel,
    three_two_one,
)
from m3_cracks import refinery_hedge, seasonality, stats

ST = stats()
RH = refinery_hedge()


def test_text():
    assert round(1.1835 * 6.28981, 2) == 7.44 and round(barrels_per_tonne(0.845), 2) == 7.44
    p = RH["prices"]
    assert round(p["wti"], 2) == 83.90
    assert round(per_gallon_to_per_barrel(p["gas_nyh"]), 2) == 134.95
    assert round(per_gallon_to_per_barrel(p["ulsd_nyh"]), 2) == 178.63
    assert round(ST["top"][1], 2) == 65.61 and ST["top"][0] == "2026-08"
    assert round(ST["top"][2], 2) == 51.06 and round(ST["top"][3], 2) == 94.73
    assert ST["top2022"][0] == "2022-05" and round(ST["top2022"][1], 2) == 62.68
    assert ST["low"][0] == "2009-11" and round(ST["low"][1], 2) == 5.51
    assert round(ST["mean"], 2) == 21.20
    assert round(ST["arb_mean"], 1) == 6.0 and ST["arb_neg"] == 35 and ST["n"] == 242
    s = {m: (g, d) for m, g, d in seasonality()}
    assert round(s[5][0], 2) == 2.83 and round(s[1][0], 2) == -3.83 and round(s[11][1], 2) == 4.15
    assert max(s, key=lambda m: s[m][1]) == 11 and max(s, key=lambda m: s[m][0]) == 5


def test_exercises():
    assert round(three_two_one(75, 2.40, 2.80), 2) == 31.40
    assert round(per_tonne_to_per_barrel(900, 0.845), 2) == 120.91
    assert round(gross_refining_margin(80, {"g": 0.47, "d": 0.30, "o": 0.30}, {"g": 100, "d": 110, "o": 60}), 2) == 18
    assert round(arbitrage_open(2.50, 2.62, 0.08), 2) == 0.04 and round(2.62 - 0.08, 2) == 2.54
    assert hedge_lots(60_000, 30, {"g": 2, "d": 1}, 3) == {"crude": 1800, "g": -1200, "d": -600}


def test_problem():
    assert RH["lots"] == {"crude": 8280, "gasoline": -5520, "diesel": -2760}
    assert round(RH["crack"], 2) == 65.61 and round(RH["margin_usd"] / 1e6, 1) == 543.3
    assert round(RH["crack"] / ST["mean"], 1) == 3.1
    assert round((round(RH["crack"], 2) - 25) * 8.28, 1) == 336.3
    assert hedge_lots(90_000, 92, {"g": 3, "d": 2}, 5) == {"crude": 8280, "g": -4968, "d": -3312}
