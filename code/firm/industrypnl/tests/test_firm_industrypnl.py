"""Acceptance tests for firm.industrypnl on synthetic panels."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_industrypnl as ip  # noqa: E402

VIX = {2019: 15.0, 2020: 30.0, 2021: 20.0, 2022: 25.0, 2023: 17.0}
FX = {y: {"USD": 1.0, "EUR": 1.1, "GBP": 1.3} for y in VIX}
CPI = {y: 100.0 + 5 * (y - 2019) for y in VIX}


def panel(noise=0.0, seed=0):
    rng = np.random.default_rng(seed)
    firms = {"A": ("maker", 2.0, 1.0), "B": ("maker", 1.0, 1.0), "C": ("venue", 0.5, 0.2), "D": ("venue", 0.8, 0.2)}
    rows = []
    for f, (k, a, b) in firms.items():
        for y, v in VIX.items():
            rph = math.exp(a + b * math.log(v) + noise * rng.standard_normal())
            rows.append(ip.Row(f, k, y, "USD", rph * 100.0 * CPI[y] / CPI[2023], 100.0, "year end", "synthetic"))
    return rows


def test_exact_recovery():
    ph = ip.per_head(panel(), FX, CPI, 2023)
    fit = ip.fe_fit(ph, VIX)
    assert abs(fit["maker"][0] - 1.0) < 1e-9 and abs(fit["venue"][0] - 0.2) < 1e-9
    assert fit["n"] == 20 and fit["firms"] == 4 and fit["dof"] == 14 and fit["r2_within"] > 0.999999


def test_noise_gives_standard_errors():
    fit = ip.fe_fit(ip.per_head(panel(0.1, 3), FX, CPI, 2023), VIX)
    b, se = fit["maker"]
    assert 0 < se < 0.5 and abs(b - 1.0) < 4 * se


def test_currency_and_deflation():
    r = ip.Row("E", "maker", 2021, "EUR", 100.0, 10.0, "average", "x")
    assert abs(ip.real_usd(r, FX, CPI, 2023) - 100.0 * 1.1 * 120.0 / 110.0) < 1e-9
    ph = ip.per_head([r], FX, CPI, 2021)
    assert abs(ph[0]["rph"] - 11.0) < 1e-12


def test_ranges_and_ratio():
    ph = ip.per_head(panel(), FX, CPI, 2023)
    rg = ip.ranges(ph)
    lo, hi, n = rg[("maker", 2020)]
    assert n == 2 and lo < hi
    assert abs(ip.ratio(ph, "A", 2020, 2023) - (30.0 / 17.0)) < 1e-9


def test_load(tmp_path):
    p = tmp_path / "p.csv"
    p.write_text("firm,kind,year,currency,revenue_m,employees,basis,source\nA,maker,2020,USD,10,5,year end,s\n"
                 "B,maker,2020,USD,,5,year end,s\n")
    rows = ip.load_panel(p)
    assert len(rows) == 1 and rows[0].revenue == 10.0
    c = tmp_path / "c.csv"
    c.write_text("year,cpi\n2020,100\n")
    assert ip.load_cpi(c) == {2020: 100.0}
