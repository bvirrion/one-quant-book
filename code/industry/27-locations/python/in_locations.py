"""One Quant Book 17, chapter 27: locations -- pay after tax and housing in five cities.

Tax: chapter 15's firm.aftertax data (tax_2026.csv; ECB 2025 average exchange rates). Rents: data/industry/rents.csv
(ONS, HUD) and two constants below whose publishers' reuse terms were not checked (ledger F3-F4): the City of Zurich's
median net rent of a three-room flat (March 2024) and Hong Kong's Rating and Valuation Department average rent per
square metre of class B flats on Hong Kong Island (August 2026, provisional) times an ILLUSTRATIVE 55 square metres.
The statistics differ in measure (average, median, 40th percentile; gross or net of charges): the chapter says so.
"""
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/locations"))
import firm_locations as fl  # noqa: E402

DATA = ROOT / "data/industry"
P = fl.at.load(DATA / "tax_2026.csv", DATA / "ch_federal_tax_2026.csv")
ZURICH_RENT = 1578.0            # CHF a month, median net rent, three rooms, City of Zurich, March 2024 (F3)
HK_RENT_M2 = 446.0              # HK$ per m2 a month, class B, Hong Kong Island, Aug 2026 provisional (F4)
HK_M2 = 55.0                    # flat size, m2 (ILLUSTRATIVE, within class B)
PACKAGE = 300_000.0
GRID = tuple(float(g) for g in range(100_000, 1_000_001, 50_000))


def cities():
    out = {}
    with open(DATA / "rents.csv") as f:
        for r in csv.DictReader(f):
            out[r["city"]] = fl.City(r["city"], r["location"], float(r["rent_month"]), r["currency"], r["measure"],
                                     r["period"], r["source"])
    out["Zurich"] = fl.City("Zurich", "zurich", ZURICH_RENT, "chf", "median net rent; three rooms; City of Zurich",
                            "2024-03", "ledger 27 F3")
    out["Hong Kong"] = fl.City("Hong Kong", "hong_kong", HK_RENT_M2 * HK_M2, "hkd",
                               "average rent per m2 of class B flats x 55 m2; Hong Kong Island", "2026-08",
                               "ledger 27 F4")
    return out


ORDER = ("London", "New York", "Chicago", "Zurich", "Hong Kong")
PLI_2024 = {"Switzerland": 184.3, "United States": 149.2, "United Kingdom": 129.1, "Netherlands": 121.0}  # F5


def table(gross=PACKAGE):
    c = cities()
    return {k: fl.disposable(P, c[k], gross) for k in ORDER}


def curves():
    c = cities()
    return {k: [fl.disposable(P, c[k], g)["disposable"] for g in GRID] for k in ORDER}


def london_new_york():
    c = cities()
    return {"crossing": fl.crossing(P, c["London"], c["New York"], 3e5, 5e6),
            "crossing_low": fl.crossing(P, c["London"], c["New York"], 5e4, 2e5),
            "ny_for_london_300k": fl.equivalent(P, c["London"], PACKAGE, c["New York"]),
            "london_for_ny_300k": fl.equivalent(P, c["New York"], PACKAGE, c["London"])}


if __name__ == "__main__":
    for k, v in table().items():
        print(k, {a: round(b) for a, b in v.items()})
    for k, v in table(1e6).items():
        print("1m", k, {a: round(b) for a, b in v.items()})
    print(london_new_york())
