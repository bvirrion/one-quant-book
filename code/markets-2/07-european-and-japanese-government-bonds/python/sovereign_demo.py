"""Chapter 7 of Book 2: European and Japanese government bonds. Monthly 10-year yields (OECD via
FRED), euro-area spreads to Germany, a decomposition of the 2011 widening, the JGB yield under
yield-curve control, and an LDI fund built like the Bank of England's stylised example."""
import csv
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/sovspread"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/bond"))
from firm_bond import Bond
from firm_sovspread import decompose, spreads

DATA = pathlib.Path(__file__).resolve().parents[4] / "data/markets-2/oecd_10y_monthly.csv"


def yields() -> dict[str, list[tuple[str, float]]]:
    out: dict[str, list[tuple[str, float]]] = {}
    with open(DATA) as f:
        for r in csv.DictReader(f):
            for k, v in r.items():
                if k != "date" and v:
                    out.setdefault(k, []).append((r["date"], float(v)))
    return out


def euro_spreads() -> dict[str, list[tuple[str, float]]]:
    y = yields()
    return spreads({k: y[k] for k in ("DE", "IT", "FR", "ES")}, "DE")


def widening_2011() -> dict[str, float]:
    y = {k: dict(v) for k, v in yields().items()}
    d = decompose(y["IT"], y["DE"], "2011-06-01", "2011-11-01")
    return {"change": d.change_bp, "italy": d.issuer_bp, "germany": d.benchmark_bp}


def latest() -> dict[str, float]:
    """The last monthly yield of each country."""
    return {k: v[-1][1] for k, v in yields().items()}


# ---- an LDI fund (illustrative), after the Bank of England's example: 2x leverage in repo ----------
GILT = Bond(1.5, dt.date(2052, 7, 22))     # an illustrative long gilt
START = dt.date(2022, 9, 22)
Y0 = 0.0350
HOLDING = 1_000_000_000.0                  # market value of gilts held, GBP
REPO_SHARE = 0.5                           # half the gilts financed in repo


def fund(shock_bp: float) -> dict[str, float]:
    """Gilt value, repo, cushion after a parallel rise of shock_bp (gilt yield only)."""
    p0 = GILT.dirty_price(Y0, START)
    face = HOLDING / p0 * 100
    value = face * GILT.dirty_price(Y0 + shock_bp / 1e4, START) / 100
    repo = HOLDING * REPO_SHARE
    leverage = value / (value - repo) if value > repo else float("inf")
    return {"price0": p0, "value": value, "repo": repo, "cushion": value - repo,
            "cushion_pct": (value - repo) / (HOLDING - repo), "leverage": leverage}


def exhaustion_bp(lo: float = 0.0, hi: float = 2000.0) -> float:
    """Yield rise that wipes out the cushion (bisection)."""
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if fund(mid)["cushion"] > 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def sales_to_relever(shock_bp: float) -> float:
    """Gilts to sell, with no new capital, to bring the repo back to half of the gilts held:
    B - S = (V - S) / 2  =>  S = 2B - V."""
    f = fund(shock_bp)
    return max(2 * f["repo"] - f["value"], 0.0)


def cushion_for_resilience(shock_bp: float = 250.0) -> float:
    """Cushion (as a share of the initial gilt holding) that survives a rise of shock_bp."""
    f = fund(shock_bp)
    return (HOLDING - f["value"]) / HOLDING


def nav_curve() -> list[tuple[int, float]]:
    return [(s, 100 * fund(s)["cushion"] / (HOLDING * (1 - REPO_SHARE))) for s in range(0, 401, 10)]
