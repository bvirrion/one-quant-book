"""Chapter 2 of Book 3: crude oil. NYMEX WTI futures, contracts 1 to 4 (EIA daily settlements,
1985 to April 2024), the spring of 2020, quality arithmetic and the storage floor."""
import csv
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/crude"))
from firm_crude import api_gravity, basket_benchmark, implied_storage_cost, quality_adjusted

DATA = pathlib.Path(__file__).resolve().parents[4] / "data/markets-3"


def load_wti() -> list[tuple[dt.date, float, float, float, float]]:
    """(date, contract 1, contract 2, contract 3, contract 4) settlements, $/bbl."""
    with open(DATA / "wti_futures_c1_c4_daily.csv") as fh:
        return [(dt.date.fromisoformat(r["date"]), float(r["c1"]), float(r["c2"]), float(r["c3"]),
                 float(r["c4"])) for r in csv.DictReader(fh)]


def spring_2020() -> list[tuple[dt.date, float, float]]:
    return [(d, c1, c2) for d, c1, c2, _, _ in load_wti() if dt.date(2020, 3, 2) <= d <= dt.date(2020, 5, 29)]


def spread_stats() -> dict[str, object]:
    """Contract 2 minus contract 1 over the whole history: the widest contango and how rare it is."""
    rows = load_wti()
    spreads = [(d, c2 - c1) for d, c1, c2, _, _ in rows]
    widest = max(spreads, key=lambda x: x[1])
    return {"n": len(rows), "first": rows[0][0], "last": rows[-1][0], "widest": widest,
            "over5": sum(1 for _, s in spreads if s > 5.0),
            "second": sorted((s for _, s in spreads), reverse=True)[1],
            "negative_c1": [d for d, c1, *_ in rows if c1 < 0]}


def april_20() -> dict[str, float]:
    """The penultimate day of the May 2020 contract, from the EIA series and the CFTC report."""
    row = {d: (c1, c2) for d, c1, c2, _, _ in load_wti()}
    near, far = row[dt.date(2020, 4, 20)]
    prev = row[dt.date(2020, 4, 17)]
    return {"near": near, "far": far, "spread": far - near, "prev_spread": prev[1] - prev[0],
            "storage": implied_storage_cost(near, far), "expiry": row[dt.date(2020, 4, 21)][0]}


def quality_examples() -> dict[str, object]:
    """A grade of specific gravity 0.827 and the most competitive grade of an illustrative basket."""
    grade, net = basket_benchmark({"Brent": 81.40, "Forties": 81.05, "Oseberg": 81.90, "Ekofisk": 81.60,
                                   "Troll": 81.75, "WTI Midland": 81.50},
                                  {"Oseberg": 0.70, "Ekofisk": 0.40, "Troll": 0.55})
    return {"api": api_gravity(0.827), "adjusted": quality_adjusted(80.0, 42.0, 0.25, 38.0, 0.40, 0.04, 0.12),
            "grade": grade, "benchmark": net}
