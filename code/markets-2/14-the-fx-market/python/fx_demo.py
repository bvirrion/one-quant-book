"""Chapter 14 of Book 2: the FX market. Pair conventions, spot dates around holidays, crosses
triangulated through the dollar, and the shares of the 2025 BIS Triennial Survey. Quotes are
illustrative, near the Federal Reserve's H.10 rates of 18 September 2026; holidays are hypothetical."""
import csv
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/fxpairs"))
from firm_fxpairs import Quote, arbitrage, cross_via_usd, spot_date, spread_pips

DATA = pathlib.Path(__file__).resolve().parents[4] / "data/markets-2"
LEGS = {"EURUSD": Quote(1.1462, 1.1464), "USDJPY": Quote(156.86, 156.88), "GBPUSD": Quote(1.3371, 1.3373),
        "USDCAD": Quote(1.4007, 1.4009)}


def crosses() -> dict[str, Quote]:
    return {"EURJPY": cross_via_usd(("EURUSD", LEGS["EURUSD"]), ("USDJPY", LEGS["USDJPY"]), "EURJPY"),
            "EURGBP": cross_via_usd(("EURUSD", LEGS["EURUSD"]), ("GBPUSD", LEGS["GBPUSD"]), "EURGBP"),
            "GBPJPY": cross_via_usd(("GBPUSD", LEGS["GBPUSD"]), ("USDJPY", LEGS["USDJPY"]), "GBPJPY")}


def relative_spread_bp(q: Quote) -> float:
    return (q.ask - q.bid) / q.mid * 1e4


def spot_examples() -> list[tuple[str, str, dt.date]]:
    tue = dt.date(2026, 10, 6)
    wed, thu = tue + dt.timedelta(days=1), tue + dt.timedelta(days=2)
    cases = [("USDJPY", "none", {}), ("USDJPY", "Japan Wednesday", {"JPY": {wed}}),
             ("USDJPY", "US Wednesday", {"USD": {wed}}), ("USDJPY", "US Thursday", {"USD": {thu}}),
             ("USDCAD", "none", {}), ("EURJPY", "Japan Wednesday", {"JPY": {wed}})]
    return [(p, h, spot_date(tue, p, hol)) for p, h, hol in cases]


def the_cross(notional_eur: float = 10e6) -> dict[str, float]:
    """The weekend problem: EURJPY from EURUSD and USDJPY, and two direct quotes."""
    syn = crosses()["EURJPY"]
    tight, crossed = Quote(179.80, 179.84), Quote(179.85, 179.87)
    return {"bid": syn.bid, "ask": syn.ask, "pips": spread_pips(syn, "EURJPY"), "rel_bp": relative_spread_bp(syn),
            "leg1_bp": relative_spread_bp(LEGS["EURUSD"]), "leg2_bp": relative_spread_bp(LEGS["USDJPY"]),
            "tight_ok": arbitrage(tight, syn) is None, "crossed": arbitrage(crossed, syn) or "",
            "profit_jpy": (crossed.bid - syn.ask) * notional_eur,
            "profit_usd": (crossed.bid - syn.ask) * notional_eur / LEGS["USDJPY"].ask,
            "usd_leg": notional_eur * LEGS["EURUSD"].ask}


def load_bis() -> list[dict[str, str]]:
    with open(DATA / "bis_triennial_2025.csv") as f:
        return list(csv.DictReader(f))
