"""Numbers gate: every numerical answer printed in Book 6, chapter 23 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_frtb as m
from firm_frtb import es_liquidity, girr_rho, rfet, scenario

S = m.sensitivities()
SA = m.standardised()
IM = m.internal_models()
DC = m.desk_capital()
P = {v: m.pla(v) for v in ("proxy_10y", "no_2y", "no_jpy", "delta_gamma")}


def mn(x, d=2):
    return round(x / 1e6, d)


def test_text():
    assert (round(S["girr"][2.0] * 1e-4), round(S["girr"][10.0] * 1e-4)) == (56_525, -155_012)
    assert round(100 * girr_rho(2, 10), 1) == 88.7
    p = SA["parts"]
    assert (mn(p["girr"]), mn(p["fx_delta"]), mn(p["fx_vega"]), mn(p["fx_curv"])) == (7.83, 5.30, 14.49, 39.23)
    assert round(100 * m.FX_RW / m.SQ2, 1) == 10.6
    assert mn(SA["low"]) == 68.29 and SA["capital"] == SA["low"]
    assert mn(IM["es_current"]["all"]) == 5.27 and IM["stress"][1] == "2022-10-03"
    es = IM["es_stressed"]
    assert (mn(es["all"]), mn(es["rates"]), mn(es["fx"])) == (14.41, 5.67, 14.01)
    assert mn(IM["imcc"]) == 17.04 and mn(IM["capital"]) == 25.56
    assert round(IM["capital"] / SA["capital"], 2) == 0.37 and round(SA["capital"] / IM["capital"], 1) == 2.7
    assert (round(P["delta_gamma"]["spearman"], 2), round(P["delta_gamma"]["ks"], 3)) == (1.00, 0.008)
    assert (round(P["no_jpy"]["spearman"], 3), round(P["no_jpy"]["ks"], 3), P["no_jpy"]["zone"]) == (0.956, 0.060, "green")
    assert (round(P["no_2y"]["spearman"], 3), round(P["no_2y"]["ks"], 3), P["no_2y"]["zone"]) == (0.949, 0.100, "amber")
    assert (round(P["proxy_10y"]["spearman"], 3), round(P["proxy_10y"]["ks"], 3), P["proxy_10y"]["zone"]) == (
        0.703, 0.044, "amber")


def test_exercises():
    r = girr_rho(2, 10)
    assert (round(100 * scenario(r, "high")), round(100 * scenario(r, "low"), 1)) == (100, 77.4)
    assert not rfet(list(range(0, 120, 4)))
    assert round(es_liquidity([5.0, 3.0]), 2) == 5.83 and round(math.sqrt(34), 2) == 5.83


def test_problem():
    assert (mn(DC["surcharge"]), mn(DC["amber_total"])) == (21.36, 46.93)
    d, lv = m.rv.data()
    assert min(v[2] for day, v in zip(d, lv, strict=True) if day.startswith("2022")) < 1.0
