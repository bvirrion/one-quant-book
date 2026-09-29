"""One Quant Book 17, chapter 8: asset owners' costs and the internal-or-external choice, from their annual reports.

data/industry/asset_owners.csv: published totals (local currency, millions; assets in billions);
data/industry/ecb_fx_annual.csv: ECB annual average rates (US dollars per unit via the euro).
"""
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/ownercost"))
import firm_ownercost as oc  # noqa: E402

DATA = ROOT / "data/industry"


def usd_per(currency, year=2025):
    with open(DATA / "ecb_fx_annual.csv") as f:
        r = {int(x["year"]): x for x in csv.DictReader(f)}[year]
    ue = float(r["usd_per_eur"])
    return {"USD": 1.0, "EUR": ue, "NOK": ue / float(r["nok_per_eur"]), "CAD": ue / float(r["cad_per_eur"])}[currency]


def owners():
    out = {}
    with open(DATA / "asset_owners.csv") as f:
        for r in csv.DictReader(f):
            ext = float(r["external_assets_bn"]) * 1000 if r["external_assets_bn"] else None
            out[r["owner"]] = dict(row=r, owner=oc.Owner(r["owner"], float(r["assets_bn"]) * 1000,
                                   float(r["internal_costs_m"]), float(r["external_base_m"]),
                                   float(r["external_perf_m"]), ext))
    return out


def nbim():
    o = owners()["NBIM"]
    r, ow = o["row"], o["owner"]
    i_bp, e_bp = oc.split_bp(ow)
    per_head_nok = float(r["personnel_m"]) / float(r["employees"])
    return dict(total_bp=oc.cost_bp(ow), internal_bp=i_bp, external_bp=e_bp, external_base_bp=1e4 * ow.external_base
                / ow.external_assets, external_share=ow.external_assets / ow.assets,
                personnel_per_head_nok_m=per_head_nok, personnel_per_head_usd_k=1000 * per_head_nok * usd_per("NOK"),
                assets_usd_bn=ow.assets / 1000 * usd_per("NOK"), assets_per_employee_usd_bn=ow.assets / 1000
                * usd_per("NOK") / float(r["employees"]))


def cpp():
    ow = owners()["CPP Investments"]["owner"]
    return dict(total_bp=oc.cost_bp(ow), operating_bp=1e4 * ow.internal_costs / ow.assets,
                external_bp=1e4 * (ow.external_base + ow.external_perf) / ow.assets, assets_usd_bn=ow.assets / 1000
                * usd_per("CAD", 2025))


def team_breakeven(heads=10, cost_per_head_k=352.0, systems_k=1500.0, fees=(10, 20, 30, 40)):
    """Break-even mandate size ($ million) for an internal team against external fees (basis points)."""
    return {f: oc.breakeven_assets(heads, cost_per_head_k / 1000, systems_k / 1000, f) for f in fees}
