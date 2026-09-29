"""Chapter 29 of One Quant Book 14: three venues, one budget (firm.connplan; the plan is the chapter's example).

    PLAN, PRICES               the firm's venues, targets and footprint; the dated price rows
    report()                   latency table, budget, checks and the cheapest fix for the missed target
    sensitivities()            the budget's change under single changes to the plan
    access_availability()      the NYSE access design's availability (circuit reliabilities are assumptions)
"""
import dataclasses
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "connplan"))
import firm_connplan as cp  # noqa: E402

V, L = cp.Venue, cp.Line
VENUES = (
    V("NYSE equities (Mahwah)", "colocated", 40.0, site="mahwah", metric="wire-to-wire p99"),
    V("CME data (Aurora to Mahwah)", "radio", 4200.0, site="aurora", published_us=3986.0,
      metric="one way"),
    V("CME orders (Mahwah to Aurora)", "fibre", 8000.0, site="aurora", factor=1.3,
      metric="one way"),
    V("Binance (AWS Tokyo)", "cloud", 1000.0, path="internet",
      offers=("internet", "endpoint_same", "endpoint_other"), metric="round trip p99"),
)
LINES = (
    L("nyse_cabinet", 1, "shared", "colocation"), L("nyse_kw", 8, "shared", "colocation"),
    L("nyse_xc", 4, "shared", "colocation"),
    L("nyse_lcn_10g", 1, "NYSE equities (Mahwah)", "connectivity"),
    L("nyse_ip_1g", 1, "NYSE equities (Mahwah)", "connectivity"),
    L("wave_mah_aur", 1, "CME orders (Mahwah to Aurora)", "connectivity"),
    L("nyse_wl_cme", 1, "CME data (Aurora to Mahwah)", "market data"),
    L("nyse_cme_feed", 1, "CME data (Aurora to Mahwah)", "market data"),
    L("aws_tokyo_c7i_4xl", 2, "Binance (AWS Tokyo)", "cloud"),
)
PLAN = cp.Plan(VENUES, LINES)
PRICES = cp.load_prices()
TODAY = "2026-09-28"


def report(plan=PLAN):
    return {"latency": cp.latency_table(plan), "budget": cp.budget(plan, PRICES),
            "checks": cp.check_prices(plan, PRICES, TODAY), "fixes": cp.cheapest_fixes(plan, PRICES)}


def with_lines(extra=(), drop=()):
    return dataclasses.replace(PLAN, lines=tuple(x for x in LINES if x.key not in drop) + tuple(extra))


def sensitivities():
    base = cp.budget(PLAN, PRICES)["annual"]
    cases = {
        "second 10 Gb LCN connection": with_lines((L("nyse_lcn_10g", 1, "NYSE equities (Mahwah)", "connectivity"),)),
        "12 kW instead of 8": with_lines((L("nyse_kw", 4, "shared", "colocation"),)),
        "no backup IP circuit": with_lines(drop=("nyse_ip_1g",)),
        "wavelength price 50% higher": with_lines((L("wave_mah_aur", 0.5, "CME orders (Mahwah to Aurora)",
                                                     "connectivity"),)),
        "four Tokyo instances": with_lines((L("aws_tokyo_c7i_4xl", 2, "Binance (AWS Tokyo)", "cloud"),)),
    }
    return {k: cp.budget(p, PRICES)["annual"] - base for k, p in cases.items()}


def access_availability():
    c = cp.sla.Circuit
    lcn = c("LCN 10 Gb", "fibre", 24000, 15000, 4000.0, 4.0, "networks/29:F1", TODAY)
    ip = c("IP network 1 Gb", "fibre", 2500, 2500, 4000.0, 4.0, "networks/15:F4", TODAY)
    return {"lcn only": cp.availability([lcn]), "lcn and ip": cp.availability([lcn, ip], 0.2, 8.0)}
