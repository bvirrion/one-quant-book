"""firm.connplan -- the connectivity plan (build of One Quant Book 14, chapter 29; the book's capstone).

Inputs, as data: venues with their access (colocated, radio, fibre or cloud), a latency target each, and a
footprint of priced items (data/prices.csv, dated rows with their ledger source). Latency comes from the book's
components: firm.cagenet and firm.wirepath for a colocated path, a published radio figure, firm.fibreroute for a
fibre route over firm.geomap's geodesic, firm.privlink for a cloud path. Contracts use firm.slamodel; the
recovery line firm.drplan. Outputs: a latency table, a bill of materials, a budget and its sensitivities, the
unmet targets with the cheapest change that meets each, checks on every price row, and the cost table exported
for Book 16 (README.md).

API (stable):
    PriceRow ; load_prices(path) -> {key: PriceRow}
    Venue(name, access, target_us, site=None, published_us=None, factor=1.3, path=None, offers=(), metric="")
    Line(key, qty, venue, category) ; Plan(venues, lines, home="mahwah", dr_share=0.25, term_months=36)
    latency_us(venue, plan) -> achieved latency in microseconds ; latency_table(plan) -> [dict]
    bom(plan, prices) -> [dict] ; budget(plan, prices) -> dict(monthly, one_time, annual, by_category, dr_annual)
    check_prices(plan, prices, today, days=60) -> dict(unsourced, stale)
    cheapest_fixes(plan, prices) -> [dict(venue, option, achieved_us, extra_annual)]
    availability(circuits, common_rate_y, common_mttr_h) ; export_cost_table(plan, prices, path)
"""
import csv
import dataclasses
import datetime as dt
import pathlib
import sys
from dataclasses import dataclass

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for c in ("geomap", "cagenet", "wirepath", "fibreroute", "privlink", "slamodel"):
    sys.path.insert(0, str(HERE.parent / c))
import firm_cagenet as cg  # noqa: E402
import firm_fibreroute as fr  # noqa: E402
import firm_geomap as gm  # noqa: E402
import firm_privlink as pl  # noqa: E402
import firm_slamodel as sla  # noqa: E402
import firm_wirepath as wp  # noqa: E402

SITES = {s.id: s for s in gm.load_sites(ROOT / "data" / "networks" / "sites.csv")}
CARD = dict(rx_p50=800.0, rx_p99=2000.0, tx_p50=800.0, tx_p99=2000.0)    # model values, as in chapter 5


@dataclass(frozen=True)
class PriceRow:
    key: str
    item: str
    vendor: str
    monthly: float
    one_time: float
    unit: str
    source: str
    as_of: str


def load_prices(path=HERE / "data" / "prices.csv"):
    with open(path) as f:
        return {r["key"]: PriceRow(r["key"], r["item"], r["vendor"], float(r["monthly"]), float(r["one_time"]),
                                   r["unit"], r["source"], r["as_of"]) for r in csv.DictReader(f)}


@dataclass(frozen=True)
class Venue:
    name: str
    access: str                 # "colocated" | "radio" | "fibre" | "cloud"
    target_us: float
    site: str = None
    published_us: float = None
    factor: float = 1.3
    path: str = None
    offers: tuple = ()
    metric: str = ""


@dataclass(frozen=True)
class Line:
    key: str
    qty: float
    venue: str
    category: str


@dataclass(frozen=True)
class Plan:
    venues: tuple
    lines: tuple
    home: str = "mahwah"
    dr_share: float = 0.25
    term_months: int = 36


def _colocated_p99(cross_connect_m=60.0):
    cage = cg.Cage([cg.Device("venue", "handoff"), cg.Device("l1", "l1", 5.0), cg.Device("server", "server")],
                   [cg.Cable("venue", "l1", cross_connect_m), cg.Cable("l1", "server", 3.0)])
    wire = wp.wire_stages(cage, cage.path("venue", "server"), cage.path("server", "venue"))
    cards = wp.card_stages(**CARD)
    stages = wire[:1] + cards[:1] + wp.book13_software() + cards[1:] + wire[1:]
    return next(r["p99"] for r in wp.report(stages) if r["stage"] == "wire-to-wire") / 1000.0


def latency_us(v, plan):
    if v.access == "colocated":
        return _colocated_p99()
    if v.access == "radio":
        return v.published_us
    if v.access == "fibre":
        a, b = SITES[plan.home], SITES[v.site]
        km = gm.geodesic_m(a.lat, a.lon, b.lat, b.lon) / 1000.0
        return fr.components(fr.build(v.name, km, v.factor))["total"]
    if v.access == "cloud":
        return pl.rtt_percentiles(pl.load_paths()[v.path])[99]
    raise ValueError(v.access)


def latency_table(plan):
    rows = []
    for v in plan.venues:
        x = latency_us(v, plan)
        rows.append({"venue": v.name, "metric": v.metric, "achieved_us": x, "target_us": v.target_us,
                     "met": x <= v.target_us})
    return rows


def bom(plan, prices):
    out = []
    for ln in plan.lines:
        p = prices[ln.key]
        m, o = ln.qty * p.monthly, ln.qty * p.one_time
        out.append({"item": p.item, "vendor": p.vendor, "venue": ln.venue, "category": ln.category, "qty": ln.qty,
                    "monthly_usd": m, "one_time_usd": o, "annual_usd": 12 * m + 12 * o / plan.term_months,
                    "source": p.source, "as_of": p.as_of, "key": ln.key})
    return out


def budget(plan, prices):
    rows = bom(plan, prices)
    by = {}
    for r in rows:
        by[r["category"]] = by.get(r["category"], 0.0) + r["annual_usd"]
    on_site = sum(r["annual_usd"] for r in rows if r["category"] in ("colocation", "connectivity"))
    dr = plan.dr_share * on_site
    by["disaster recovery"] = dr
    return {"monthly": sum(r["monthly_usd"] for r in rows), "one_time": sum(r["one_time_usd"] for r in rows),
            "annual": sum(r["annual_usd"] for r in rows) + dr, "by_category": by, "dr_annual": dr}


def check_prices(plan, prices, today, days=60):
    t = dt.date.fromisoformat(today)
    keys = {ln.key for ln in plan.lines}
    unsourced = sorted(k for k in keys if not prices[k].source)
    stale = sorted(k for k in keys if (t - dt.date.fromisoformat(prices[k].as_of)).days > days)
    return {"unsourced": unsourced, "stale": stale}


def cheapest_fixes(plan, prices, bytes_per_month=0.0):
    """Each cloud venue missing its target: the offered paths that meet it, cheapest first."""
    fixes = []
    paths = pl.load_paths()
    for v in plan.venues:
        if v.access != "cloud" or latency_us(v, plan) <= v.target_us:
            continue
        for option in v.offers:
            alt = dataclasses.replace(v, path=option)
            x = latency_us(alt, plan)
            if x <= v.target_us:
                p = paths[option]
                extra = 12 * (p.usd_hour * 730 + p.usd_per_gb * bytes_per_month / 1e9)
                fixes.append({"venue": v.name, "option": option, "achieved_us": x,
                              "extra_annual": extra})
    return sorted(fixes, key=lambda f: f["extra_annual"])


def availability(circuits, common_rate_y=0.0, common_mttr_h=8.0):
    return sla.design_availability(sla.Design("plan", tuple(circuits), common_rate_y, common_mttr_h))


def export_cost_table(plan, prices, path):
    cols = ["item", "vendor", "venue", "category", "qty", "monthly_usd", "one_time_usd", "annual_usd", "source",
            "as_of"]
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in bom(plan, prices):
            w.writerow([r[c] if not isinstance(r[c], float) else f"{r[c]:.2f}" for c in cols])
