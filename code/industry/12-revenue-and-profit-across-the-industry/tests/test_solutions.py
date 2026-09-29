"""Numbers gate: every numerical answer printed in Book 17, chapter 12 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_industry as a  # noqa: E402

ip = a.ip
PH = a.per_head()


def r(x, d=2):
    return round(float(x), d)


def test_panel_size_and_sources():
    rs = a.regression_set(PH)
    assert len(rs) == 87 and len({p["firm"] for p in rs}) == 15
    assert all(row.source for row in a.rows())
    kinds = {p["firm"]: p["kind"] for p in rs}
    assert sum(1 for k in kinds.values() if k == "exchange or venue") == 6
    assert sum(1 for k in kinds.values() if k == "market maker") == 3


def test_latest_table():
    fr = {x["firm"]: x for x in a.firm_ranges(PH)}
    want = {"Nasdaq": 0.55, "Man Group": 0.77, "Intercontinental Exchange": 0.77, "Morgan Stanley": 0.85,
            "Flow Traders": 0.86, "MarketAxess": 0.94, "Goldman Sachs": 1.23, "Tradeweb": 1.31, "Coinbase": 1.45,
            "Cboe Global Markets": 1.46, "CME Group": 1.68, "Interactive Brokers": 1.77, "Virtu Financial": 2.16,
            "Optiver": 2.57, "Quadrature Capital Limited": 9.29}
    assert {f: r(fr[f]["last_v"]) for f in want} == want
    assert r(fr["Quadrature Capital Limited"]["last_v"] / fr["Nasdaq"]["last_v"], 1) == 16.9


def test_spread_and_swings():
    s = a.spread(PH)
    assert s["lo"][0] == "Nasdaq" and r(s["lo"][1]) == 0.48
    assert s["hi"][0] == "Quadrature Capital Limited" and r(s["hi"][1], 1) == 13.0 and s["factor"] > 20
    assert r(s["swings"]["Flow Traders"], 1) == 4.5 and r(s["swings"]["Virtu Financial"], 1) == 2.5
    assert r(s["swings"]["CME Group"], 1) == 1.2
    fr = {x["firm"]: x for x in a.firm_ranges(PH)}
    assert r(fr["Nasdaq"]["lo"]) == 0.48


def test_ice_and_profit_per_head():
    rows = {(x.firm, x.year): x for x in a.rows()}
    assert rows[("Intercontinental Exchange", 2025)].revenue == 9931.0
    assert 12640 - 9931 == 2709 and 412 + 2297 == 2709
    pp = a.profit_per_head()
    assert r(pp["Quadrature Capital Limited"]["local"]) == 3.22 and r(pp["Quadrature Capital Limited"]["usd"]) == 4.11
    assert r(pp["CME Group"]["usd"]) == 1.09 and r(pp["Virtu Financial"]["usd"]) == 1.07
    assert r(pp["Optiver"]["local"]) == 0.65 and r(pp["Optiver"]["usd"]) == 0.71


def test_entity_and_price_level():
    e = a.entity_rows(PH)
    assert [(y, round(n)) for y, _, n in e] == [(2022, 96), (2023, 51), (2024, 26), (2025, 21)]
    assert r(e[0][1]) == 1.00 and r(e[-1][1]) == 7.18
    c = a.cpi()
    assert r(c[2025] / c[2019]) == 1.26


def test_regimes():
    v = a.vix()
    assert [v[y] for y in range(2019, 2026)] == [15.39, 29.25, 19.66, 25.64, 16.85, 15.55, 18.93]
    assert r(v[2020] / v[2023]) == 1.74
    m = a.mm_ratios(PH)
    assert r(m["Virtu Financial"]) == 2.16 and r(m["Flow Traders"]) == 4.51


def test_elasticities():
    f = a.fit(PH)
    want = {"market maker": (1.19, 0.26), "exchange or venue": (0.13, 0.16), "asset manager": (0.23, 0.27),
            "bank (whole firm)": (0.03, 0.32), "broker": (-0.39, 0.37), "crypto exchange": (-1.27, 0.59)}
    assert {k: (r(f[k][0]), r(f[k][1])) for k in want} == want
    assert f["n"] == 87 and f["firms"] == 15 and round(100 * f["r2_within"]) == 30
    assert r((a.vix()[2020] / a.vix()[2023]) ** f["market maker"][0]) == 1.92


def test_small_runs():
    rs = [p for p in a.regression_set(PH) if p["kind"] not in ("crypto exchange", "broker")]
    f2 = ip.fe_fit(rs, a.vix())
    f = a.fit(PH)
    assert abs(f2["market maker"][0] - f["market maker"][0]) < 1e-9
    assert abs(f2["exchange or venue"][0] - f["exchange or venue"][0]) < 1e-9
    assert r(f2["market maker"][1]) == 0.26 and r(f2["exchange or venue"][1]) == 0.16


def test_medians_and_cell_example():
    km = a.kind_medians(PH)
    ys = range(2019, 2026)
    assert [r(km[("market maker", y)]) for y in ys] == [0.90, 2.70, 1.62, 1.24, 0.96, 1.77, 1.51]
    assert [r(km[("exchange or venue", y)]) for y in ys] == [1.31, 1.27, 1.23, 1.13, 1.05, 1.10, 1.31]
    assert [r(km[("bank (whole firm)", y)]) for y in ys] == [1.20, 1.37, 1.28, 0.90, 1.08, 0.99, 1.04]
    fx, c = a.fx(), a.cpi()
    local = 933.425 / 554
    assert r(local) == 1.68 and r(fx[2020]["EUR"], 4) == 1.1422 and r(local * fx[2020]["EUR"]) == 1.92
    assert r(c[2025]) == 135.83 and r(c[2020]) == 109.20
    fr = {(p["firm"], p["year"]): p["rph"] for p in PH}
    assert r(fr[("Flow Traders", 2020)]) == 2.39 and r(fr[("Flow Traders", 2023)]) == 0.53
