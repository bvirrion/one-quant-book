"""Acceptance tests of firm.riskengine (Book 6, chapter 29), incl. the fixture shared with C++ and Rust."""
import datetime as dt
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_riskengine as re_

fp = re_.fp
T0 = dt.date(2026, 9, 23)


def fixture():
    pnl = np.array([[10 * math.sin(0.7 * i + j) + 3 * math.cos(1.3 * i * (j + 1)) for j in range(5)]
                    for i in range(40)])
    paths = [("F", "A", "x"), ("F", "A", "y"), ("F", "B", "x"), ("F", "B", "x"), ("F", "B", "z")]
    return pnl, paths


def test_kernel_fixture():
    pnl, paths = fixture()
    agg = re_.aggregate(pnl, paths)
    rep = re_.risk_report(agg, 0.95, 0.90)
    assert len(agg) == 7
    assert abs(rep[("F",)]["var"] - 14.86618942343704) < 1e-9 and abs(rep[("F",)]["es"] - 14.291194493251536) < 1e-9
    assert abs(rep[("F", "B")]["var"] - 26.518767856515673) < 1e-9
    e = re_.euler_es(agg[("F",)], {k: v for k, v in agg.items() if len(k) == 2}, 0.90)
    assert abs(e[("F", "A")] - 1.114894308826234) < 1e-9 and abs(sum(e.values()) - rep[("F",)]["es"]) < 1e-9
    assert np.allclose(agg[("F",)], pnl.sum(axis=1))


def market():
    c = re_.PillarCurve(T0, (0.04,) * 8)
    return fp.MarketData(asof=T0, spots={"EURUSD": 1.15}, curves={"USD": c},
                         dividends={"EURUSD": fp.Dividends(div_yield=0.02)},
                         vols={"EURUSD": fp.FlatVol(0.08), "USD": fp.FlatVol(0.009)}, funding={"EURUSD": "USD"})


def test_rates_instruments_registered():
    md = market()
    sw = re_.IRSwap(id="s", underlying="USD", currency="USD", notional=1.0, years=5, fixed=0.0)
    df5 = md.df("USD", re_.add_years(T0, 5))
    assert abs(fp.price(sw, md, re_.NormalRates()).pv - (1 - df5)) < 1e-12
    par = (1 - df5) / sum(md.df("USD", re_.add_years(T0, i)) for i in range(1, 6))
    at_par = re_.IRSwap(id="p", underlying="USD", currency="USD", years=5, fixed=par)
    assert abs(fp.price(at_par, md, re_.NormalRates()).pv) < 1e-14
    exp = re_.add_years(T0, 1)
    pay = re_.Swaption(id="a", underlying="USD", currency="USD", expiry=exp, tenor=5, strike=0.04)
    rec = re_.Swaption(id="b", underlying="USD", currency="USD", expiry=exp, tenor=5, strike=0.04, payer=False)
    fwd_pv = fp.price(pay, md, re_.NormalRates()).pv - fp.price(rec, md, re_.NormalRates()).pv
    ann = sum(md.df("USD", re_.add_years(exp, i)) for i in range(1, 6))
    fwd = (md.df("USD", exp) - md.df("USD", re_.add_years(exp, 5))) / ann
    assert abs(fwd_pv - ann * (fwd - 0.04)) < 1e-14          # put-call parity on swaptions
    d = fp.instrument_from_dict(pay.to_dict())
    assert d == pay


def test_pillar_bump_and_factors():
    md = market()
    ids = [f.id for f in md.risk_factors()]
    assert "CURVE:USD:10Y" in ids and "SPOT:EURUSD" in ids
    b = md.apply(fp.Bump("CURVE:USD:10Y", 1e-4))
    assert b.curves["USD"].zero(10.0) - 0.04 > 0.99e-4 and b.curves["USD"].zero(1.0) == 0.04


def test_methods_agree_on_small_moves_and_count_calls():
    md = market()
    trades = [re_.Trade("s", re_.IRSwap(id="s", underlying="USD", currency="USD", notional=1e6, years=10,
                                        fixed=0.04), 1.0, ("F", "R")),
              re_.Trade("o", fp.EuropeanOption(id="o", underlying="EURUSD", currency="USD", notional=1e6,
                                               strike=1.15, expiry=T0 + dt.timedelta(days=90), right="C"),
                        -1.0, ("F", "X"))]
    factors = [f"CURVE:USD:{p}" for p in re_.PILLARS] + ["SPOT:EURUSD"]
    rng = np.random.default_rng(1)
    moves = np.hstack([rng.normal(0, 2e-5, (20, 8)), rng.normal(0, 1e-4, (20, 1))])
    sc = re_.historical_scenarios([str(i) for i in range(20)], factors, moves, [False] * 8 + [True])
    out = {}
    for name, f in re_.METHODS.items():
        c = re_.Counter()
        out[name] = (f(trades, md, sc, c), c.calls)
    assert out["full"][1] == 2 * 21 and out["delta-gamma"][1] == (1 + 16) + (1 + 18)
    assert out["grid"][1] == (1 + 8 * 6) + (1 + 9 * 6)
    for name in ("grid", "delta-gamma"):
        assert np.allclose(out[name][0], out["full"][0], rtol=0, atol=2.0)
    c = re_.Counter()
    plan = re_.planned_revaluation(trades, md, sc, c, {("F",): "delta-gamma", ("F", "X"): "full"})
    assert np.allclose(plan[:, 1], out["full"][0][:, 1]) and np.allclose(plan[:, 0], out["delta-gamma"][0][:, 0])
    assert c.calls == 17 + 21


def test_limits():
    rep = {("F",): {"var": 10.0}, ("F", "A"): {"var": 3.0}}
    assert re_.check_limits(rep, {("F",): 8.0, ("F", "A"): 5.0}) == [(("F",), 10.0, 8.0)]


def test_failing_trade_does_not_stop_the_run():
    md = market()
    good = re_.Trade("s", re_.IRSwap(id="s", underlying="USD", currency="USD", years=5, fixed=0.04), 1.0, ("F",))
    bad = re_.Trade("x", fp.EuropeanOption(id="x", underlying="XYZ", currency="USD", strike=1.0,
                                           expiry=re_.add_years(T0, 1), right="C"), 1.0, ("F",))
    sc = re_.historical_scenarios(["a"], ["CURVE:USD:5Y"], np.array([[1e-4]]), [False])
    c = re_.Counter()
    pnl = re_.full_revaluation([good, bad], md, sc, c)
    assert np.isfinite(pnl[0, 0]) and np.isnan(pnl[0, 1]) and len(c.errors) == 2
