"""Acceptance tests of the Book 5, Chapter 7 build (volatility surface)."""
import datetime as dt
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "bs"))
from firm_bs import black
from firm_volsurface import arbitrage_report, density_factor, from_vols, risk_neutral_density

A = dt.date(2026, 9, 24)
EXP = [A + dt.timedelta(days=d) for d in (91, 182, 365)]
KS = [round(-0.4 + 0.05 * j, 2) for j in range(17)]


def smile(k, t):
    return 0.2 - 0.1 * k / math.sqrt(t) + 0.2 * k * k / math.sqrt(t)


def surface(vols=None):
    ts = [(e - A).days / 365 for e in EXP]
    vols = vols or [[smile(k, t) for k in KS] for t in ts]
    return from_vols(A, EXP, [100.0 * math.exp(0.02 * t) for t in ts], KS, vols)


def test_nodes_are_reproduced():
    s = surface()
    for e in EXP:
        t = (e - A).days / 365
        for k in KS:
            strike = s.forward(t) * math.exp(k)
            assert abs(s.implied_vol(strike, e) - smile(k, t)) < 1e-12


def test_flat_surface_is_clean():
    s = surface([[0.2] * len(KS) for _ in EXP])
    assert arbitrage_report(s) == {"calendar": [], "butterfly": []}
    assert abs(density_factor(0.01, 0.0, 0.0, 0.0) - 1.0) < 1e-12


def test_bad_quotes_are_caught():
    ts = [(e - A).days / 365 for e in EXP]
    vols = [[smile(k, t) for k in KS] for t in ts]
    vols[1][KS.index(-0.1)] += 0.03
    assert arbitrage_report(surface(vols))["butterfly"]
    vols = [[smile(k, t) for k in KS] for t in ts]
    vols[2] = [v - 0.08 for v in vols[2]]
    assert arbitrage_report(surface(vols))["calendar"]


def test_breeden_litzenberger_recovers_lognormal():
    f, t, v, df = 100.0, 0.5, 0.2, 0.99
    ks = [60 + 0.25 * i for i in range(321)]
    dens = risk_neutral_density(ks, [black(f, k, t, df, v, "C") for k in ks], df)
    for k, q in dens[::40]:
        s = v * math.sqrt(t)
        exact = math.exp(-0.5 * ((math.log(k / f) + 0.5 * s * s) / s) ** 2) / (k * s * math.sqrt(2 * math.pi))
        assert abs(q - exact) < 1e-5
