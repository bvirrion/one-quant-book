"""Chapter 5 of Book 2: repo and specials. September 2019 (FRED), FICC sponsored repo (OFR), the
carry of a financed note, and the value of specialness over an auction cycle (illustrative)."""
import csv
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/repo"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/bond"))
from firm_bond import Bond
from firm_repo import RepoTrade, carry, fails_charge, margin_call, special_rate_floor, value_of_specialness

DATA = pathlib.Path(__file__).resolve().parents[4] / "data/markets-2"


def sept_2019() -> list[dict[str, float | str]]:
    with open(DATA / "repo_sept2019.csv") as f:
        return [{"date": r["date"], **{k: float(v) for k, v in r.items() if k != "date"}} for r in csv.DictReader(f)]


def sponsored() -> list[tuple[str, float, float]]:
    with open(DATA / "ficc_sponsored.csv") as f:
        return [(r["date"], float(r["repo_usdbn"]), float(r["reverse_repo_usdbn"])) for r in csv.DictReader(f)]


# ---- a financed position: the ten-year note of Chapter 3 ---------------------------------------
TEN = Bond(4.25, dt.date(2036, 8, 15))
SETTLE = dt.date(2026, 9, 25)
GC = 0.0390


def financed_note(days: int = 30) -> dict[str, float]:
    dirty = TEN.dirty_price(0.042, SETTLE)
    c = carry(100e6, 4.25, dirty, GC, days, period_days=184)
    dv01 = TEN.risk(0.042, SETTLE)["dv01"] * 1e6          # USD per bp on 100 million
    trade = RepoTrade("repo", "T 4.25 08/36", 100e6, dirty, 0.02, GC, SETTLE, SETTLE + dt.timedelta(days=days))
    return {"dirty": dirty, "carry": c, "dv01": dv01, "breakeven_bp": c / dv01, "cash": trade.cash,
            "interest": trade.interest(), "margin_after_fall": margin_call(trade, dirty - 1.5, SETTLE)}


# ---- specialness over an auction cycle (illustrative levels) ------------------------------------
PATH = [(30, 0.0045), (30, 0.0025), (30, 0.0010)]     # (days, specialness) until the next auction


def specialness_curve() -> list[tuple[int, float]]:
    """Daily specialness in basis points over the 90 days (step path, as in PATH)."""
    out, day = [], 0
    for days, s in PATH:
        for _ in range(days):
            out.append((day, s * 1e4))
            day += 1
    return out


def special_value() -> dict[str, float]:
    dirty = TEN.dirty_price(0.042, SETTLE)
    v = value_of_specialness(dirty, PATH)
    dv01_100 = TEN.risk(0.042, SETTLE)["dv01"]            # price points per bp, per 100
    return {"points": v, "thirty_seconds": v * 32, "yield_bp": v / dv01_100,
            "usd_per_100m": v / 100 * 100e6}


__all__ = ["fails_charge", "special_rate_floor"]
