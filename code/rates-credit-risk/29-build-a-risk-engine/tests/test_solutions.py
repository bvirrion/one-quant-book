"""Numbers gate: every numerical answer printed in Book 6, chapter 29 (text and solutions)."""
import collections
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import numpy as np
import rc_riskengine as m

M = 1e6


def pct(x):
    return round(100 * x, 2)


def test_market_and_scenarios():
    z = m.market().curves["USD"].zeros
    assert (round(100 * z[0], 2), round(100 * z[-1], 2)) == (4.49, 5.40)
    x = np.array([[b.size for b in s.bumps] for s in m.scenarios(10)])
    assert round(1e4 * np.abs(x[:, :8]).max()) == 48 and round(100 * np.abs(x[:, 8]).max(), 1) == 2.8


def test_book():
    b = m.book()
    c = collections.Counter(t.path[-1] for t in b)
    assert (c["Swaps"], c["Options"], c["Short-dated"], c["Long-dated"]) == (600, 200, 89, 111)
    assert sum(t.path[-1] == "Short-dated" and t.quantity < 0 for t in b) == 71


def test_calls_and_hours():
    r = m.revaluations(10)
    calls = {k: v["calls"] for k, v in r.items()}
    assert calls == {"full": 251_000, "grid": 50_200, "delta-gamma": 17_400, "plan": 86_604}
    assert m.revaluations(1)["plan"]["calls"] == 86_604
    assert 800 * 49 + 200 * 55 == 50_200 and 800 * 17 + 200 * 19 == 17_400
    assert 200 * 251 + 111 * 19 + 600 * 49 + 89 * 55 == 86_604
    hours = {k: round(m.wall_clock(v), 2) for k, v in calls.items()}
    assert hours == {"full": 4.36, "grid": 0.87, "delta-gamma": 0.30, "plan": 1.50}
    assert round(4 * 3600 * 16 / (50_000 * 0.02), 1) == 230.4


def test_errors():
    w1, w10 = m.worst(1), m.worst(10)
    assert (pct(w1["grid"]), pct(w1["delta-gamma"])) == (1.59, 0.74)
    assert (pct(w10["grid"]), pct(w10["delta-gamma"]), pct(w10["plan"])) == (8.64, 18.45, 0.76)
    e = m.errors(10)
    assert pct(e["delta-gamma"][("Firm", "FX", "Short-dated")]["var"]) == 18.45
    assert min(abs(e[k][("Firm", "Rates", "Options")]["var"]) for k in ("grid", "delta-gamma")) > 0.086
    assert pct(e["delta-gamma"][("Firm", "FX", "Long-dated")]["var"]) == 0.43
    assert pct(e["grid"][("Firm", "FX", "Long-dated")]["var"]) == -2.17
    assert pct(max(abs(v["var"]) for v in m.errors(1)["grid"].values())) == 1.59


def test_report():
    r = m.reports(10)["full"]
    f, rates, fx = r[("Firm",)], r[("Firm", "Rates")], r[("Firm", "FX")]
    assert (round(f["var"] / M, 2), round(f["es"] / M, 2)) == (53.53, 50.89)
    assert (round(fx["es"] / M, 2), round(rates["es"] / M, 2)) == (14.63, 47.34)
    assert round((rates["es"] + fx["es"]) / M, 2) == 61.96 and round((rates["es"] + fx["es"] - f["es"]) / M, 2) == 11.07
    e = m.euler()
    assert (round(e[("Firm", "FX")] / M, 2), round(e[("Firm", "Rates")] / M, 2)) == (3.56, 47.34)
    lim = m.limits()
    assert len(lim) == 1 and lim[0][0] == ("Firm", "FX", "Short-dated")
    assert round(lim[0][1] / M, 2) == 14.58 and lim[0][2] == 12e6
