"""Acceptance tests of the pricing library core (INTERFACES.md section 1)."""
import datetime as dt
import json
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "bs"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "curve"))
import firm_pricing as fp
from firm_bs import bs
from firm_bs import greeks as bs_greeks

T0 = dt.date(2026, 9, 24)
EXP = T0 + dt.timedelta(days=365)


def market(**kw):
    base = dict(asof=T0, spots={"ABC": 100.0}, curves={"USD": fp.FlatCurve(0.05, T0)}, vols={"ABC": fp.FlatVol(0.2)})
    base.update(kw)
    return fp.MarketData(**base)


def call(**kw):
    a = dict(id="c1", underlying="ABC", currency="USD", strike=100.0, expiry=EXP, right="C")
    a.update(kw)
    return fp.EuropeanOption(**a)


def test_price_equals_black_scholes():
    r = fp.price(call(), market())
    assert abs(r.pv - bs(100, 100, 1.0, 0.05, 0.0, 0.2, "C")) < 1e-12 and r.engine == "Analytic" and r.currency == "USD"


def test_forward_with_cash_proportional_and_borrow():
    div = fp.Dividends(cash=((T0 + dt.timedelta(days=100), 2.0),), proportional=((T0 + dt.timedelta(days=200), 0.01),),
                       borrow=0.003)
    md = market(dividends={"ABC": div})
    f = md.forward("ABC", EXP)
    expected = (100 - 2 * math.exp(-0.05 * 100 / 365)) * 0.99 * math.exp(-0.003) * math.exp(0.05)
    assert abs(f - expected) < 1e-12


def test_american_put_by_tree_and_european_consistency():
    md = market()
    eu = fp.price(call(right="P"), md).pv
    tree_eu = fp.price(call(right="P"), md, engine=fp.TreeEngine(1001)).pv
    am = fp.price(call(right="P", exercise="american"), md).pv
    assert abs(tree_eu - eu) < 1e-4 and am > eu + 0.4


def test_greeks_desk_units_against_analytic():
    g = fp.greeks(call(notional=10.0), market(), which=("delta", "gamma", "vega", "theta", "rho", "vanna", "volga"),
                  bumps=fp.GreekBumps(spot_rel=1e-4, vol_abs=1e-4, rate_abs=1e-6))
    a = bs_greeks(100, 100, 1.0, 0.05, 0.0, 0.2, "C")
    assert abs(g["delta"] - 10 * a["delta"]) < 1e-6
    assert abs(g["gamma"] - 10 * a["gamma"] * 100 ** 2 / 100) < 1e-4
    assert abs(g["vega"] - 10 * a["vega"] * 0.01) < 1e-6
    assert abs(g["rho"] - 10 * a["rho"] * 1e-4) < 1e-7
    assert abs(g["theta"] - 10 * a["theta"] / 365) < 5e-4
    assert abs(g["vanna"] - 10 * a["vanna"] * 0.01) < 5e-4 and abs(g["volga"] - 10 * a["volga"] * 1e-4) < 5e-4


def test_sensitivities_keys_units_and_time():
    md = market(dividends={"ABC": fp.Dividends()})
    s = fp.sensitivities(call(), md, ["SPOT:ABC", "VOL:ABC", "CURVE:USD", "DIV:ABC", "BORROW:ABC", "TIME"])
    a = bs_greeks(100, 100, 1.0, 0.05, 0.0, 0.2, "C")
    assert abs(s["SPOT:ABC"] - a["delta"] * 1.0) < 1e-3            # per 1 % of spot = delta * S / 100
    assert abs(s["VOL:ABC"] - a["vega"] * 0.01) < 1e-4
    assert s["DIV:ABC"] < 0 and s["BORROW:ABC"] < 0 and s["TIME"] < 0 and s["CURVE:USD"] > 0


def test_bucketed_vega_sums_to_parallel_vega():
    md = market()
    exps = [T0 + dt.timedelta(days=d) for d in (91, 182, 365, 730)]
    ks = [70.0, 85.0, 100.0, 115.0, 130.0]
    bv = fp.bucketed_vega(call(), md, exps, ks)
    total = sum(bv.values())
    assert abs(total - fp.greeks(call(), md, which=("vega",))["vega"]) < 2e-3
    assert max(bv, key=bv.get) == (exps[2], 100.0)


def test_risk_factors_and_node_bump():
    md = market(vols={"ABC": fp.grid_from(market(), "ABC", [EXP], [90.0, 100.0, 110.0])},
                dividends={"ABC": fp.Dividends()}, fx={"EURUSD": 1.15}, correlations={frozenset({"ABC", "XYZ"}): 0.5})
    ids = {f.id for f in md.risk_factors()}
    assert {"SPOT:ABC", "VOL:ABC", f"VOL:ABC:{EXP.isoformat()}:100", "CURVE:USD", "DIV:ABC", "BORROW:ABC",
            "FX:EURUSD", "CORR:ABC|XYZ", "TIME"} <= ids
    b = md.apply(fp.Bump(f"VOL:ABC:{EXP.isoformat()}:100", 0.01))
    assert abs(b.vols["ABC"].implied_vol(100.0, EXP) - 0.21) < 1e-12 and md.vols["ABC"].implied_vol(100.0, EXP) == 0.2
    assert abs(md.apply(fp.Bump("CORR:ABC|XYZ", 0.8)).correlations[frozenset({"ABC", "XYZ"})] - 1.0) < 1e-12
    assert abs(md.apply(fp.Bump("FX:EURUSD", 0.01, True)).fx_rate("USD", "EUR") - 1 / (1.15 * 1.01)) < 1e-12


def test_snapshot_immutable_and_rolled():
    md = market()
    md.apply(fp.Bump("SPOT:ABC", 0.1, True), fp.Bump("TIME", 30))
    assert md.spots["ABC"] == 100.0 and md.asof == T0
    r = md.rolled(T0 + dt.timedelta(days=30))
    assert abs(r.df("USD", EXP) - math.exp(-0.05 * 335 / 365)) < 1e-12


def test_book2_curve_conforms_and_parallel_shift():
    from firm_curve import Curve
    c = Curve(T0, [1.0, 2.0], [math.exp(-0.05), math.exp(-0.10)])
    md = market(curves={"USD": c})
    assert isinstance(c, fp.DiscountCurve) and abs(fp.price(call(), md).pv - bs(100, 100, 1.0, 0.05, 0, 0.2, "C")) < 1e-9
    up = md.apply(fp.Bump("CURVE:USD", 1e-4))
    assert abs(up.df("USD", EXP) - math.exp(-0.0501)) < 1e-12
    with pytest.raises(fp.PricingError):
        md.apply(fp.Bump("CURVE:USD:5Y", 1e-4))


def test_reprice_and_batch_with_error_slot():
    md = market()
    book = [(call(), 2.0), (call(id="p1", right="P"), -1.0)]
    sc = [fp.Scenario("up10", (fp.Bump("SPOT:ABC", 0.10, True),)), fp.Scenario("volup", (fp.Bump("VOL:ABC", 0.05),))]
    r = fp.reprice(book, md, sc)
    manual = 2 * (fp.price(call(), md.apply(*sc[0].bumps)).pv - fp.price(call(), md).pv) - (
        fp.price(call(id="p1", right="P"), md.apply(*sc[0].bumps)).pv - fp.price(call(id="p1", right="P"), md).pv)
    assert abs(r["up10"] - manual) < 1e-12
    bad = fp.EuropeanOption(id="x", underlying="NOPE", currency="USD", strike=1.0, expiry=EXP, right="C")
    res = fp.price_batch(book + [(bad, 1.0)], [md, md.apply(*sc[1].bumps)])
    assert res.pv.shape == (2, 3) and np.isnan(res.pv[0, 2]) and (0, 2) in res.errors and not np.isnan(res.pv[1, 0])


def test_json_round_trips():
    i = call(exercise="american")
    back = fp.instrument_from_dict(json.loads(json.dumps(i.to_dict())))
    assert back == i
    s = fp.Scenario("s", (fp.Bump("SPOT:ABC", 0.01, True),))
    assert fp.Scenario.from_dict(json.loads(json.dumps(s.to_dict()))) == s
    d = json.loads(json.dumps(market(dividends={"ABC": fp.Dividends(cash=((EXP, 1.0),))}).to_dict()))
    assert d["dividends"]["ABC"]["cash"][0][1] == 1.0 and d["curves"]["USD"]["rate"] == 0.05


def test_seed_is_stable_and_unsalted():
    import zlib
    assert fp.seed_for(call()) == fp.seed_for(call(strike=90.0)) == zlib.crc32(b"c1")


def test_register_bump_kind():
    def credit(md, b):
        return md
    fp.register_bump("CREDIT2", credit)
    assert market().apply(fp.Bump("CREDIT2:X", 1e-4)).spots["ABC"] == 100.0
    with pytest.raises(fp.PricingError):
        market().apply(fp.Bump("NOSUCH:X", 1.0))


def test_unsupported_combination_raises():
    with pytest.raises(fp.PricingError):
        fp.price(call(exercise="american"), market(), engine=fp.AnalyticEngine())
