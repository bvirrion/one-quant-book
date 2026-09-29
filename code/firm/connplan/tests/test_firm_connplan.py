import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_connplan as cp  # noqa: E402

P = cp.load_prices()


def _plan(**kw):
    v = (cp.Venue("cloud venue", "cloud", 1000.0, path="internet", offers=("internet", "endpoint_same")),
         cp.Venue("radio venue", "radio", 5000.0, published_us=4000.0))
    lines = (cp.Line("nyse_kw", 8, "shared", "colocation"), cp.Line("wave_mah_aur", 1, "radio venue", "connectivity"))
    return cp.Plan(v, lines, **kw)


def test_prices_have_dates_and_most_have_sources():
    assert all(p.as_of for p in P.values()) and [k for k, p in P.items() if not p.source] == ["wave_mah_aur"]


def test_budget_by_hand():
    b = cp.budget(_plan(dr_share=0.0), P)
    assert b["monthly"] == 8 * 1200 + 20000 and b["one_time"] == 10000
    assert abs(b["annual"] - (12 * (9600 + 20000) + 12 * 10000 / 36)) < 1e-9


def test_checks_and_fixes():
    plan = _plan()
    c = cp.check_prices(plan, P, "2026-09-28")
    assert c == {"unsourced": ["wave_mah_aur"], "stale": []}
    assert cp.check_prices(plan, P, "2026-12-31")["stale"] == ["nyse_kw", "wave_mah_aur"]
    t = cp.latency_table(plan)
    assert [r["met"] for r in t] == [False, True]
    f = cp.cheapest_fixes(plan, P)
    assert f[0]["option"] == "endpoint_same" and f[0]["achieved_us"] < 1000.0


def test_fibre_and_export(tmp_path):
    plan = cp.Plan((cp.Venue("f", "fibre", 1e9, site="aurora", factor=1.0),), ())
    floor = cp.gm.floor_us(cp.gm.geodesic_m(cp.SITES["mahwah"].lat, cp.SITES["mahwah"].lon, cp.SITES["aurora"].lat,
                                            cp.SITES["aurora"].lon), "fibre")
    assert abs(cp.latency_us(plan.venues[0], plan) - floor) < 2.0          # glass plus amplifiers
    out = tmp_path / "cost.csv"
    cp.export_cost_table(_plan(), P, out)
    rows = list(csv.DictReader(open(out)))
    assert [r["source"] for r in rows] == ["networks/29:F1", ""] and rows[0]["annual_usd"] == "115200.00"
