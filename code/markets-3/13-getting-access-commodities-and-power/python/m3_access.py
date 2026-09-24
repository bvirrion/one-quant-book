"""Chapter 13 of Book 3: getting access to commodity and power markets. Three routes into German
power for a stated trading plan, and the collateral a new entrant posts before trading 50 MW
baseload for a year. Every fee, margin rate and funding rate here is illustrative."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/nominate"))
from firm_nominate import carry_cost

HOURS = 8760
PRICE = 85.0                     # EUR/MWh, a year of baseload (illustrative)
FUNDING = 0.05                   # cost of funding collateral, a year (illustrative)


def baseload(mw: float = 50.0) -> dict[str, float]:
    mwh = mw * HOURS
    return {"mwh": mwh, "notional": mwh * PRICE}


def routes(mw: float = 50.0) -> list[dict[str, float | str]]:
    """Annual fixed cost and collateral of three routes (illustrative):
    exchange through a clearing member: 12% initial margin, EUR 60,000 of fees and data;
    bilateral OTC through a broker: a letter of credit for two months of deliveries at 1.5% a year,
    EUR 25,000 of brokerage for this volume;
    physical as a balancing responsible party: security of EUR 500,000, EUR 150,000 of staff and
    systems, and the imbalance risk."""
    n = baseload(mw)["notional"]
    ex_coll = 0.12 * n
    lc = 2 / 12 * n
    out = [
        {"route": "exchange", "collateral": ex_coll, "fixed": 60_000.0, "carry": carry_cost(ex_coll, FUNDING)},
        {"route": "OTC", "collateral": lc, "fixed": 25_000.0, "carry": lc * 0.015},
        {"route": "physical BRP", "collateral": 500_000.0, "fixed": 150_000.0, "carry": carry_cost(500_000.0, FUNDING)},
    ]
    for r in out:
        r["annual"] = r["fixed"] + r["carry"]
    return out


def first_trade(mw: float = 50.0) -> dict[str, float]:
    """The weekend problem: the firm posts exchange margin on the year of baseload and the balancing-group
    security; it requires from its buyer a letter of credit for two months of deliveries, which the buyer
    arranges and pays for."""
    n = baseload(mw)["notional"]
    margin, security, lc = 0.12 * n, 500_000.0, 2 / 12 * n
    return {"notional": n, "margin": margin, "security": security, "posted": margin + security, "lc": lc,
            "lc_fee": lc * 0.015, "carry": carry_cost(margin + security, FUNDING)}
