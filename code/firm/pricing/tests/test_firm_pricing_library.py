"""Acceptance tests of the Chapter 28 additions to the pricing library: every new instrument through every engine that
supports it, against closed forms and the chapter components, JSON, common random numbers and bucketed vega."""
import datetime as dt
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "bs"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "pathdep"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "calib"))
import firm_pricing as fp
from firm_bs import bs
from firm_calib import lewis_calls
from firm_pathdep import forward_start_call

T0 = dt.date(2026, 9, 24)
E = dt.date(2027, 9, 24)
MONTHS = tuple(T0 + dt.timedelta(days=30 * i) for i in range(1, 13))


def market(**kw):
    base = dict(asof=T0, spots={"ABC": 100.0, "XYZ": 50.0}, curves={"USD": fp.FlatCurve(0.03, T0)},
                vols={"ABC": fp.FlatVol(0.2), "XYZ": fp.FlatVol(0.25)}, dividends={"ABC": fp.Dividends(div_yield=0.01)},
                correlations={frozenset(("ABC", "XYZ")): 0.5}, funding={"ABC": "USD", "XYZ": "USD"})
    base.update(kw)
    return fp.MarketData(**base)


def euro(**kw):
    a = dict(id="o", underlying="ABC", currency="USD", strike=100.0, expiry=E, right="C")
    a.update(kw)
    return fp.EuropeanOption(**a)


def test_pde_and_monte_carlo_against_the_analytic_engine():
    md = market()
    for right, k in (("C", 100.0), ("P", 90.0)):
        o = euro(right=right, strike=k)
        exact = fp.price(o, md).pv
        assert abs(fp.price(o, md, engine=fp.PDEEngine()).pv - exact) < 5e-3
        assert abs(fp.price(o, md, engine=fp.MonteCarloEngine()).pv - exact) < 0.1
    am = euro(right="P", exercise="american", strike=110.0)
    assert abs(fp.price(am, md, engine=fp.PDEEngine()).pv - fp.price(am, md, engine=fp.TreeEngine()).pv) < 5e-3
    no_div = market(dividends={})
    assert abs(fp.price(euro(exercise="american"), no_div, engine=fp.PDEEngine()).pv
               - fp.price(euro(), no_div, engine=fp.PDEEngine()).pv) < 1e-9


def test_closed_forms():
    md = market()
    dig = fp.DigitalOption(id="d", underlying="ABC", currency="USD", strike=105.0, expiry=E, right="C")
    t, df = md.t(E), md.df("USD", E)
    d2 = (math.log(md.forward("ABC", E) / 105.0) - 0.02 * t) / (0.2 * math.sqrt(t))
    assert abs(fp.price(dig, md).pv - df * 0.5 * math.erfc(-d2 / math.sqrt(2))) < 1e-7
    put_dig = fp.DigitalOption(id="d", underlying="ABC", currency="USD", strike=105.0, expiry=E, right="P")
    assert abs(fp.price(dig, md).pv + fp.price(put_dig, md).pv - df) < 1e-12
    assert abs(fp.price(dig, md, engine=fp.MonteCarloEngine()).pv - fp.price(dig, md).pv) < 0.005
    fs = fp.ForwardStart(id="f", underlying="ABC", currency="USD", start=T0 + dt.timedelta(days=146), expiry=E, right="C")
    r, q = 0.03, 0.01
    assert abs(fp.price(fs, md).pv - forward_start_call(100.0, 1.0, md.t(fs.start), t, r, q, 0.2)) < 1e-9
    vs = fp.VarianceSwap(id="v", underlying="ABC", currency="USD", strike_vol=0.2, expiry=E, vega_notional=1.0)
    assert abs(fp.price(vs, md).pv) < 2e-4                                    # flat 20 %: fair strike 20
    grid = fp.GridSurface(T0, (E,), (60.0, 80.0, 100.0, 120.0, 140.0), ((0.30, 0.25, 0.20, 0.18, 0.17),), (101.0,))
    assert fp.price(vs, market(vols={"ABC": grid, "XYZ": fp.FlatVol(0.25)})).pv > 0.005   # a skew lifts the strip


def test_barriers_asian_basket_worst_of():
    md = market()
    b = dict(id="b", underlying="ABC", currency="USD", strike=100.0, expiry=E, right="C", barrier=85.0, kind="DO")
    cont, daily = fp.BarrierOption(**b), fp.BarrierOption(**b, monitoring="daily")
    b_in = fp.BarrierOption(**{**b, "kind": "DI"})
    assert abs(fp.price(cont, md).pv + fp.price(b_in, md).pv - fp.price(euro(), md).pv) < 1e-9     # in + out
    assert abs(fp.price(daily, md).pv - fp.price(daily, md, engine=fp.MonteCarloEngine()).pv) < 0.08
    asian = fp.AsianOption(id="a", underlying="ABC", currency="USD", strike=100.0, expiry=MONTHS[-1], right="C",
                           fixing_dates=MONTHS)
    assert 0.5 * fp.price(euro(), md).pv < fp.price(asian, md).pv < fp.price(euro(), md).pv
    one = fp.BasketOption(id="o", underlying="ABC", currency="USD", underlyings=("ABC",), weights=(1.0,), initial=(100.0,),
                          strike=1.0, expiry=E, right="C")
    assert abs(100 * fp.price(one, md).pv - fp.price(euro(), md, engine=fp.MonteCarloEngine()).pv) < 1e-9  # same id: same draws
    wo = dict(id="w", underlying="ABC", currency="USD", underlyings=("ABC", "XYZ"), initial=(100.0, 50.0), strike=1.0,
              expiry=E, right="P")
    lo = fp.price(fp.WorstOf(**wo), md.apply(fp.Bump("CORR:ABC|XYZ", 0.3))).pv
    assert lo < fp.price(fp.WorstOf(**wo), md).pv                             # higher correlation, cheaper worst-of put


def test_autocall_tarf_cliquet_convertible_heston():
    md = market()
    obs = tuple(T0 + dt.timedelta(days=365 * i) for i in (1, 2, 3))
    ac = fp.Autocallable(id="ac", underlying="ABC", currency="USD", notional=100.0, underlyings=("ABC",), initial=(100.0,),
                         obs_dates=obs, coupon=6.0)
    assert 95 < fp.price(ac, md).pv < 106
    tarf = fp.TARF(id="t", underlying="ABC", currency="USD", strike=100.0, target=1e9, leverage=0.0, fixing_dates=MONTHS)
    strip = sum(bs(100.0, 100.0, md.t(d), 0.03, 0.01, 0.2, "P") for d in MONTHS)
    assert abs(fp.price(tarf, md).pv - strip) < 0.1                           # no leverage, no target: a strip of puts
    cl = fp.Cliquet(id="c", underlying="ABC", currency="USD", reset_dates=(T0 + dt.timedelta(days=1), *MONTHS),
                    local_floor=-1.0, local_cap=10.0, global_floor=-10.0)
    assert abs(fp.price(cl, md).pv) < 0.02                                    # sum of forward returns, drift small
    cb = fp.ConvertibleBond(id="cb", underlying="ABC", currency="USD", maturity=T0 + dt.timedelta(days=5 * 365), ratio=0.8)
    v0 = fp.price(cb, md, model=fp.CreditBlackScholes(hazard=0.0)).pv
    v1 = fp.price(cb, md, model=fp.CreditBlackScholes(hazard=0.05)).pv
    assert v1 < v0 and v0 > 80.0
    h = fp.HestonModel(0.04, 1.5, 0.04, 0.6, -0.7)
    ref = float(lewis_calls(h.cf_model(), md.forward("ABC", E), [100.0], md.t(E), df=md.df("USD", E))[0])
    assert abs(fp.price(euro(), md, model=h).pv - ref) < 1e-6


def test_json_crn_and_bucketed_vega():
    md = market()
    insts = [fp.DigitalOption(id="d", underlying="ABC", currency="USD", strike=1.0, expiry=E, right="C"),
             fp.AsianOption(id="a", underlying="ABC", currency="USD", strike=1.0, expiry=E, right="C", fixing_dates=MONTHS),
             fp.Autocallable(id="x", underlying="ABC", currency="USD", underlyings=("ABC",), initial=(1.0,), obs_dates=(E,)),
             fp.ConvertibleBond(id="cb", underlying="ABC", currency="USD", maturity=E, call_start=E)]
    for i in insts:
        assert fp.instrument_from_dict(json.loads(json.dumps(i.to_dict()))) == i
    asian = fp.AsianOption(id="a2", underlying="ABC", currency="USD", strike=100.0, expiry=MONTHS[-1], right="C",
                           fixing_dates=MONTHS)
    assert fp.price(asian, md).pv == fp.price(asian, md).pv
    grid = fp.GridSurface(T0, (T0 + dt.timedelta(days=182), E), (80.0, 100.0, 120.0), ((0.2,) * 3, (0.2,) * 3), (101.0, 102.0))
    mdg = market(vols={"ABC": grid, "XYZ": fp.FlatVol(0.25)})
    bv = fp.bucketed_vega(asian, mdg, grid.expiries, grid.strikes)
    par = fp.greeks(asian, mdg, which=("vega",))["vega"]
    assert abs(sum(bv.values()) - par) < 0.02 * abs(par)
    noisy = fp.MonteCarloEngine(crn=False)
    up = fp.price(asian, mdg.apply(fp.Bump("VOL:ABC", 0.01)), engine=noisy).pv
    dn = fp.price(asian, mdg.apply(fp.Bump("VOL:ABC", -0.01)), engine=noisy).pv
    assert abs((up - dn) / 2 - par) > 1e-4                                    # without common numbers the bump is noisy
    assert [e.name for e in fp.engines_for(euro(), fp.BlackScholes())] == ["Analytic", "Tree", "PDE", "MonteCarlo"]
