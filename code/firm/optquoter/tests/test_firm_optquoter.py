import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_optquoter as oq  # noqa: E402


def _setup():
    c = oq.Chain()
    s = oq.surface()
    return c, s, oq.mass_quote(c, 100.0, s)


def test_quotes_bracket_theo():
    c, s, q = _setup()
    assert len(q) == len(c.strikes) * len(c.expiries_days) * 2
    for x in q:
        assert x["bid"] <= x["theo"] <= x["ask"]
        assert math.isclose(x["ask"] - x["theo"], max(0.5 * x["vega"], 0.01), rel_tol=1e-9)


def test_sweep_and_protection():
    c, s, q = _setup()
    losses = [oq.sweep(q, 0.01, c, s, oq.Protection(n))["loss"] for n in (1, 5, 20, 10**9)]
    assert losses == sorted(losses)
    r = oq.sweep(q, 0.01, c, s, oq.Protection(5))
    assert r["fills"] == 5 and r["delta_shares"] < 0
    full = oq.sweep(q, 0.01, c, s, oq.Protection(10**9))
    assert math.isclose(full["loss"], full["max_loss"])
    slow = oq.sweep(q, 0.0, c, s, oq.Protection(10**9), dvol=0.02, vega_limit=1000.0, react_us=50.0)
    fast = oq.sweep(q, 0.0, c, s, oq.Protection(10**9), dvol=0.02, vega_limit=1000.0, react_us=5.0)
    assert fast["loss"] < slow["loss"] < full["loss"] + 1e9


def test_normal_day_and_refit():
    loose = oq.normal_day(170, oq.Protection(20))
    tight = oq.normal_day(170, oq.Protection(5))
    assert loose["lost"] == 0 and tight["lost"] > 0 and tight["pulls"] > 0
    c, s, _ = _setup()
    ks = np.array(c.strikes)
    vols = np.array([s.vol(k, 30 / 365, 100.0) for k in ks])
    _, rms = oq.refit_slice(ks, 100.0, 30 / 365, vols)
    assert rms < 0.002
