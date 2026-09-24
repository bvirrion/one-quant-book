"""Chapter 4 of Book 3: natural gas and LNG. Monthly benchmark prices (Henry Hub from the EIA; the
IMF's EU and Asia LNG benchmarks), and a US Gulf cargo's netback to Europe and to Asia. Route
lengths, charter rate, boil-off and regasification fees are illustrative round numbers."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/lngarb"))
from firm_lngarb import Route, breakeven_spread, choose, eur_mwh_to_usd_mmbtu, fob_price, lift

DATA = pathlib.Path(__file__).resolve().parents[4] / "data/markets-3"
CARGO = 3.5e6                                          # MMBtu, a large conventional carrier (illustrative)
EUROPE = Route("europe", 14, 60_000, 0.001, 0.50)       # US Gulf to north-west Europe (illustrative)
ASIA = Route("asia", 25, 60_000, 0.001, 0.40)           # US Gulf to north Asia via Panama (illustrative)


def load_gas() -> list[dict[str, object]]:
    """(month, Henry Hub, EU hub, Asia LNG), $/MMBtu monthly averages."""
    with open(DATA / "gas_monthly.csv") as fh:
        return [{"month": r["month"], "hh": float(r["hh"]), "eu": float(r["eu"]), "jp": float(r["jp"])}
                for r in csv.DictReader(fh)]


def cargo_month(row: dict[str, object]) -> dict[str, object]:
    """Destination, netback and lift decision of a US cargo in a month (fee sunk, slope 1.15)."""
    fob = fob_price(row["hh"])
    best, nb = choose({"europe": row["eu"], "asia": row["jp"]}, {"europe": EUROPE, "asia": ASIA}, CARGO, fob)
    return {"month": row["month"], "fob": fob, "dest": best, "netback": nb, "lift": lift(nb, row["hh"])}


def history(first: str = "2016-03") -> list[dict[str, object]]:
    return [cargo_month(r) for r in load_gas() if r["month"] >= first]


def summary() -> dict[str, object]:
    h = history()
    gas = load_gas()
    peak = max(gas, key=lambda r: r["eu"])
    return {"n": len(h), "asia": sum(1 for c in h if c["dest"] == "asia"),
            "not_lifted": [c["month"] for c in h if not c["lift"]], "peak": peak,
            "spread": breakeven_spread(EUROPE, ASIA, CARGO, fob_price(3.0))}


def conversion_example() -> float:
    """A TTF price of EUR 40/MWh at EURUSD 1.16, in USD/MMBtu."""
    return eur_mwh_to_usd_mmbtu(40.0, 1.16)
