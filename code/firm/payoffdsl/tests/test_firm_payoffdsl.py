"""Acceptance tests of firm.payoffdsl (One Quant Book 15, chapter 19)."""
import datetime as dt
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_payoffdsl as D  # noqa: E402

FP = D.FP
ASOF = dt.date(2026, 1, 5)


def md():
    return FP.MarketData(ASOF, {"U": 100.0}, {"USD": FP.FlatCurve(0.02, ASOF)}, vols={"U": FP.FlatVol(0.2)})


def test_parse_and_errors():
    p = D.parse("state x = 1; at d { if S > 100 and not (x == 2) { pay max(S - 100, 0); x = 2; } else { stop; } }")
    assert [s[0] for s in p.states] == ["x"] and p.events[0][0] == "d"
    with pytest.raises(D.ScriptError) as e:
        D.parse("at d {\n  pay S + ;\n}")
    assert (e.value.line, e.value.col) == (2, 11)
    with pytest.raises(D.ScriptError):
        D.parse("at d { pay foo(1); }")
    with pytest.raises(D.ScriptError):
        D.parse("at d { pay 1 @ 2; }")


def test_schedule_order():
    p = D.parse("at a { pay 1; } at b { pay 2; }")
    d1, d2 = ASOF + dt.timedelta(1), ASOF + dt.timedelta(2)
    assert D.schedule(p, {"a": [d2, d1], "b": [d1]}) == [(d1, 0), (d1, 1), (d2, 0)]
    with pytest.raises(D.ScriptError):
        D.schedule(p, {"a": [d1]})


def test_interpreter_equals_compiled():
    p = D.parse("""state m = 0; state lo = 9;
        at all { lo = min(lo, perf); if perf >= 0.9 { pay c + m; m = 0; } else { m = m + c; } }
        at calls { if perf >= 1.0 { pay 100; stop; } }
        at last { if lo < 0.6 { pay 100 * perf; } else { pay 100; } }""")
    rng = np.random.default_rng(3)
    perf = np.exp(np.cumsum(0.2 * rng.standard_normal((500, 4)), axis=1))
    events = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 2)]
    args = (perf, 100 * perf, events, np.array([0.5, 1, 1.5, 2]), np.array([0.99, 0.98, 0.97, 0.96]), {"c": 3.0})
    a = D.Interpreter(p).run(*args)
    b = D.compile_program(p)(*args)
    assert np.allclose(a, b) and a.std() > 0


def test_scripted_european_prices_like_the_library():
    exp = ASOF + dt.timedelta(days=365)
    s = D.ScriptedInstrument(id="E", underlying="U", currency="USD", script="at x { pay max(S - 100, 0); }",
                             dates=(("x", (exp,)),))
    e = FP.EuropeanOption(id="E", underlying="U", currency="USD", strike=100.0, expiry=exp, right="C")
    ps = FP.price(s, md()).pv
    pm = FP.price(e, md(), engine=FP.MonteCarloEngine()).pv
    pa = FP.price(e, md()).pv
    assert ps == pytest.approx(pm, rel=1e-12) and abs(ps - pa) < 0.1
    assert FP.greeks(s, md(), which=("delta",))["delta"] == pytest.approx(0.58, abs=0.02)


def test_lazy_price_and_observers():
    q = D.Quote(1.0)
    lp = D.LazyPrice(lambda x: 2 * x, q)
    top = D.LazyPrice(lambda x: x + 1, lp)
    assert top.value == 3.0 and lp.calculations == 1
    q.set(2.0)
    q.set(3.0)
    assert lp.stale and top.stale and lp.calculations == 1
    assert top.value == 7.0 and lp.calculations == 2 and top.calculations == 2
    q.set(3.0)
    assert not lp.stale
