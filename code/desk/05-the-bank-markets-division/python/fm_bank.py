"""One Quant Book 16, chapter 5: the bank markets division under its capital constraints.

Six illustrative desks ($ billions a year and of balance sheet): revenue, costs, risk-weighted assets, leverage
exposure and stress loss, chosen so that the division's leverage exposure is about four times its RWA, as for a
markets business heavy in financing. A published bank's figures (data/desk/bank_capital_jpm.csv) set the scale
of the requirements: a common equity requirement of 11.5 per cent of RWA and a leverage requirement of 5 per cent.
"""
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/bankdesk"))
import firm_bankdesk as bd  # noqa: E402

DESKS = [
    bd.Desk("flow rates", 4.0, 2.4, 60.0, 250.0, 3.0),
    bd.Desk("repo", 2.0, 0.6, 15.0, 400.0, 0.8),
    bd.Desk("prime services", 3.0, 1.2, 45.0, 200.0, 2.0),
    bd.Desk("equity derivatives", 5.0, 2.8, 70.0, 120.0, 5.0),
    bd.Desk("FX", 3.5, 2.0, 30.0, 80.0, 1.5),
    bd.Desk("credit", 2.5, 1.6, 50.0, 60.0, 3.5),
]
KEYS = bd.Keys(k_rwa=0.13, k_le=0.05, tax=0.25)
HURDLE = 0.12


def jpm():
    with open(ROOT / "data/desk/bank_capital_jpm.csv") as f:
        return {r["item"]: float(r["value"]) for r in csv.DictReader(f)}


def jpm_requirements():
    """Capital each rule requires of the published bank, $ billions: CET1 for its ratio requirement, Tier 1 for the
    risk-based Tier 1 requirement and for the leverage requirement."""
    j = jpm()
    return {"cet1_rwa": j["cet1_requirement_pct"] / 100 * j["rwa_standardized_musd"] / 1e3,
            "tier1_rwa": j["tier1_requirement_pct"] / 100 * j["rwa_standardized_musd"] / 1e3,
            "tier1_leverage": j["slr_requirement_pct"] / 100 * j["total_leverage_exposure_musd"] / 1e3,
            "le_over_rwa": j["total_leverage_exposure_musd"] / j["rwa_standardized_musd"],
            "cib_roe_check": j["cib_net_income_musd"] / (j["cib_equity_2025_busd"] * 1e3)}


def roae_table():
    eq = bd.allocate(DESKS, KEYS)
    return {k: bd.roae(DESKS, v, KEYS.tax) for k, v in eq.items()}, eq


def division():
    eq = bd.allocate(DESKS, KEYS)
    p = sum(d.profit(KEYS.tax) for d in DESKS)
    return {"profit": p, "equity_binding": eq["binding"].sum(), "roe_binding": p / eq["binding"].sum(),
            "equity_rwa": eq["rwa"].sum(), "equity_le": eq["leverage"].sum(),
            "group_rwa_req": KEYS.k_rwa * sum(d.rwa for d in DESKS),
            "group_le_req": KEYS.k_le * sum(d.le for d in DESKS)}


def charge_rate(hurdle=HURDLE):
    """Balance-sheet charge per unit of leverage exposure: the cost of the equity the leverage rule requires."""
    return hurdle * KEYS.k_le


def charged_profits(hurdle=HURDLE):
    c = charge_rate(hurdle)
    return {d.name: bd.balance_sheet_charge(d, c, KEYS.tax) for d in DESKS}


def mix(equity=None):
    """Optimal scale of each desk (0 to 1.5) with the equity the binding requirements hold today."""
    e = division()["group_le_req"] if equity is None else equity
    return bd.optimal_mix(DESKS, e, KEYS, 1.5)


def franchise(cut=0.5, prime_loss=0.20):
    """Cut the repo desk by `cut`; prime services loses `prime_loss` of its revenue and costs scale with it."""
    base = division()
    desks = []
    for d in DESKS:
        if d.name == "repo":
            desks.append(bd.Desk(d.name, d.revenue * (1 - cut), d.cost * (1 - cut), d.rwa * (1 - cut),
                                 d.le * (1 - cut), d.stress * (1 - cut)))
        elif d.name == "prime services":
            f = 1 - prime_loss
            desks.append(bd.Desk(d.name, d.revenue * f, d.cost, d.rwa * f, d.le * f, d.stress * f))
        else:
            desks.append(d)
    p = sum(x.profit(KEYS.tax) for x in desks)
    eq = bd.allocate(desks, KEYS)["binding"].sum()
    return {"profit": p, "equity": eq, "roe": p / eq, "base_roe": base["roe_binding"], "base_profit": base["profit"]}
