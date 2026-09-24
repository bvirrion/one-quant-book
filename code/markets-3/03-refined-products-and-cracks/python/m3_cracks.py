"""Chapter 3 of Book 3: refined products and cracks. Monthly averages of daily EIA spot prices
(WTI Cushing; New York Harbor conventional gasoline and ULSD; US Gulf Coast gasoline),
July 2006 to August 2026, via FRED."""
import csv
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/cracks"))
from firm_cracks import hedge_lots, per_gallon_to_per_barrel, three_two_one

DATA = pathlib.Path(__file__).resolve().parents[4] / "data/markets-3"


def load_products() -> list[dict[str, object]]:
    with open(DATA / "products_monthly.csv") as fh:
        return [{"month": r["month"], **{k: float(r[k]) for k in ("wti", "gas_nyh", "ulsd_nyh", "gas_gulf")}}
                for r in csv.DictReader(fh)]


def crack_series() -> list[tuple[str, float, float, float]]:
    """(month, 3-2-1 crack, gasoline crack, diesel crack), $/bbl of crude."""
    out = []
    for r in load_products():
        g, d = per_gallon_to_per_barrel(r["gas_nyh"]), per_gallon_to_per_barrel(r["ulsd_nyh"])
        out.append((r["month"], three_two_one(r["wti"], r["gas_nyh"], r["ulsd_nyh"]), g - r["wti"], d - r["wti"]))
    return out


def seasonality(first: str = "2010-01", last: str = "2025-12") -> list[tuple[int, float, float]]:
    """Mean gasoline and diesel crack by calendar month minus each crack's mean, $/bbl."""
    rows = [c for c in crack_series() if first <= c[0] <= last]
    g_all, d_all = np.mean([c[2] for c in rows]), np.mean([c[3] for c in rows])
    out = []
    for m in range(1, 13):
        sel = [c for c in rows if int(c[0][5:]) == m]
        out.append((m, float(np.mean([c[2] for c in sel]) - g_all), float(np.mean([c[3] for c in sel]) - d_all)))
    return out


def arb_series() -> list[tuple[str, float]]:
    """New York Harbor minus US Gulf Coast gasoline, cents per gallon."""
    return [(r["month"], 100 * (r["gas_nyh"] - r["gas_gulf"])) for r in load_products()]


def stats() -> dict[str, object]:
    cs = crack_series()
    top = max(cs, key=lambda c: c[1])
    low = min(cs, key=lambda c: c[1])
    y2022 = max((c for c in cs if c[0].startswith("2022")), key=lambda c: c[1])
    arb = [a for _, a in arb_series()]
    return {"n": len(cs), "mean": float(np.mean([c[1] for c in cs])), "top": top, "low": low, "top2022": y2022,
            "arb_mean": float(np.mean(arb)), "arb_neg": sum(1 for a in arb if a < 0)}


def refinery_hedge(throughput_bpd: float = 90_000, days: int = 92) -> dict[str, object]:
    """The weekend problem: lock a 3-2-1 margin for a quarter at the August 2026 averages taken as
    futures prices (illustrative)."""
    aug = [r for r in load_products() if r["month"] == "2026-08"][0]
    lots = hedge_lots(throughput_bpd, days, {"gasoline": 2, "diesel": 1}, 3)
    c = three_two_one(aug["wti"], aug["gas_nyh"], aug["ulsd_nyh"])
    return {"lots": lots, "crack": c, "margin_usd": c * throughput_bpd * days, "prices": aug}
