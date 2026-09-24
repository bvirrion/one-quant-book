"""Chapter 9 of Book 3: agriculturals and softs. Managed money's net position in CBOT corn (CFTC
disaggregated Commitments of Traders, futures only, 2016-2026), monthly maize and cocoa prices (IMF
via FRED), and a limit-locked position after a report."""
import csv
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/cot"))
from firm_cot import limit_path, net_share, variable_limit, zscore

DATA = pathlib.Path(__file__).resolve().parents[4] / "data/markets-3"
BUSHELS = 5_000


def load_cot() -> list[dict[str, object]]:
    with open(DATA / "cot_corn_disagg.csv") as fh:
        return [{k: (v if k == "date" else int(v)) for k, v in r.items()} for r in csv.DictReader(fh)]


def load_ags() -> list[tuple[str, float, float]]:
    with open(DATA / "ags_monthly.csv") as fh:
        return [(r["month"], float(r["cocoa"]), float(r["maize"])) for r in csv.DictReader(fh)]


def mm_series() -> list[tuple[str, float, float | None]]:
    """(report date, managed money net share of open interest, its 3-year trailing z-score)."""
    rows = load_cot()
    share = [net_share(r, "mm") for r in rows]
    return list(zip([r["date"] for r in rows], share, zscore(share, 156), strict=True))


def mm_stats() -> dict[str, object]:
    s = mm_series()
    hi = max(s, key=lambda x: x[1])
    lo = min(s, key=lambda x: x[1])
    return {"n": len(s), "max": hi[:2], "min": lo[:2], "last": s[-1], "short_weeks": sum(1 for x in s if x[1] < 0)}


def monthly_mm_vs_maize() -> list[tuple[str, float, float]]:
    """Month, mean managed money net share, IMF maize price ($/t) for months with both."""
    by: dict[str, list[float]] = {}
    for d, sh, _ in mm_series():
        by.setdefault(d[:7], []).append(sh)
    maize = {m: z for m, _, z in load_ags()}
    return [(m, float(np.mean(v)), maize[m]) for m, v in sorted(by.items()) if m in maize]


def cocoa_stats() -> dict[str, object]:
    rows = load_ags()
    peak = max(rows, key=lambda r: r[1])
    before = [r[1] for r in rows if r[0].startswith("2022")]
    return {"peak": peak[:2], "mean_2022": float(np.mean(before)), "last": rows[-1][:2]}


def report_day(contracts: int = 50, start: float = 4.50, fair: float = 3.70) -> dict[str, object]:
    """A long position caught by a report that moves the fair price of corn from `start` to `fair`."""
    lim, exp = variable_limit(start)
    path = limit_path(start, fair, lim, exp)
    locked = [d for d in path if d.locked]
    margin_per = (start - locked[-1].settle) * BUSHELS if locked else 0.0
    return {"limits": (lim, exp), "path": path, "locked_days": len(locked),
            "margin_per_contract": margin_per, "margin_total": margin_per * contracts,
            "loss_total": (start - fair) * BUSHELS * contracts}
