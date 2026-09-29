"""One Quant Book 16, chapter 19: five strategies, three latency tiers and the arms race ($ million a year).

Venue fees per tier come from Book 14's published schedules (firm.colobill): tier 1 two 1Gb connections; tier 2 a
colocation cabinet with two 10Gb ultra-low-latency connections; tier 3 two cabinets, four 10Gb connections and a
disaster-recovery link. Hardware, network routes and people are illustrative inputs. Each strategy has four rivals
whose tiers are given; the race shares (alpha) are illustrative, set against the finding that races are about a fifth
of volume and a third of the cost of liquidity in the studied market.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/techtier"))
import firm_techtier as tt  # noqa: E402

FOOTPRINTS = {
    "tier 1": [("miax-pearl", [("conn_1g", 2)])],
    "tier 2": [("nasdaq-ny11-4", [("uhd_cabinet", 1), ("cabinet_install", 1), ("power_install_p3", 1)]),
               ("miax-pearl", [("ull_10g", 2)])],
    "tier 3": [("nasdaq-ny11-4", [("uhd_cabinet", 2), ("cabinet_install", 2), ("power_install_p3", 2), ("pdu_p3", 2)]),
               ("miax-pearl", [("ull_10g", 4), ("dr_10g", 1)])],
}
OTHER = {"tier 1": 0.25, "tier 2": 0.90, "tier 3": 3.50}      # servers, FPGAs, wireless routes, engineers (inputs)


def tiers(other=None):
    other = {**OTHER, **(other or {})}
    fees = tt.colobill_venue_fees(FOOTPRINTS)
    return [tt.Tier(k, fees[k] / 1e6, other[k]) for k in FOOTPRINTS]


STRATEGIES = [tt.Strategy("futures market making", 60.0, 0.80), tt.Strategy("ETF arbitrage", 30.0, 0.90),
              tt.Strategy("equity statistical arbitrage", 20.0, 0.10), tt.Strategy("options market making", 40.0, 0.50),
              tt.Strategy("crypto basis", 10.0, 0.30)]
RIVALS = {"futures market making": [2, 2, 1, 0], "ETF arbitrage": [2, 1, 1, 0],
          "equity statistical arbitrage": [1, 0, 0, 0], "options market making": [1, 1, 1, 0],
          "crypto basis": [0, 0, 0, 0]}


def choices():
    t = tiers()
    out = {}
    for s in STRATEGIES:
        b, profits = tt.best_tier(s, t, RIVALS[s.name])
        out[s.name] = {"best": b, "profits": profits}
    return out


def races(n=5, other=None):
    t = tiers(other)
    return {s.name: tt.waste(s, t, n) for s in STRATEGIES}


def industry(other=None):
    r = races(other=other)
    spend = sum(v["spend"] for v in r.values())
    base = sum(v["baseline"] for v in r.values())
    return {"spend": spend, "baseline": base, "wasted_share": (spend - base) / spend}


PROJECTS = [("new venue connections", 1.5), ("FPGA feed handler upgrade", 1.8), ("research platform", 0.7)]


def budget():
    """Run: the chosen tiers' recurring costs and production support; change: the year's projects."""
    t = tiers()
    items = [(f"{s.name} infrastructure", t[c["best"]].annual, "run") for s, c in zip(STRATEGIES, choices().values(),
                                                                                         strict=True)]
    items.append(("production support", 1.2, "run"))
    items += [(n, a, "change") for n, a in PROJECTS]
    return items, tt.run_change(items)


VIRTU = ROOT / "data/desk/filings_virtu.csv"


def virtu():
    import csv
    with open(VIRTU) as f:
        return [(int(r["year"]), float(r["revenue"]), float(r["comm_data"])) for r in csv.DictReader(f)]
