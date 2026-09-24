"""Book 3, Chapter 28: a margin spiral across three assets, its forced-sale multiplier, the rise in
correlation in the stress, stability under a finer time step, and the ablation of each mechanism; and
the March 2020 moves in Treasury yields and the dollar."""
import csv
import dataclasses as dc
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/marginspiral"))
from firm_marginspiral import Params, correlation, forced_sale_multiplier, simulate  # noqa: E402

ABLATIONS = {"base case": {}, "8 steps a day": {"substeps": 8}, "no margin spiral": {"margin_spiral": False},
             "no loss spiral": {"loss_spiral": False}, "no price impact": {"impact": (0.0, 0.0, 0.0)},
             "one asset per holder": {"cross_holding": False}}


def run(**kw):
    return simulate(dc.replace(Params(), **kw))


def ablation_table() -> list[tuple[str, float, float, float]]:
    """(case, forced sales in USD billion, forced-sale multiplier, correlation of assets 1 and 2 in the stress)."""
    out = []
    for name, kw in ABLATIONS.items():
        r = run(**kw)
        out.append((name, r.forced_sales / 1e9, forced_sale_multiplier(r), correlation(r, 0, 1, range(10, 20))))
    return out


def price_paths() -> list[tuple[int, float, float, float]]:
    r = run()
    return [(d, *r.prices[d]) for d in range(len(r.prices))]


def correlations() -> tuple[float, float]:
    r = run()
    return correlation(r, 0, 1, range(0, 10)), correlation(r, 0, 1, range(10, 20))


def march_2020(path: str | None = None) -> list[tuple[str, float, float]]:
    path = path or str(ROOT / "data/markets-3/march2020_daily.csv")
    return [(r["date"], float(r["ust10y_pct"]), float(r["usd_broad_index"])) for r in csv.DictReader(open(path))]
