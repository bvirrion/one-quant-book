"""Chapter 15 of One Quant Book 14: buying circuits, and what two of them are worth (firm.slamodel).

    ASSUME                    failure behaviour and costs assumed by the model (not published statistics)
    designs()                 single circuit, two circuits in one duct, two diverse circuits
    results(years)            steady-state and simulated downtime, cost, credits and trading loss per design
    monthly_credits(design)   a year of monthly uptimes against a published credit schedule
    price_rows()              published monthly prices for the orders-of-magnitude table
"""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "slamodel"))
import firm_slamodel as sm  # noqa: E402

ASSUME = {"mtbf_h": 4383.0, "mttr_h": 4.0, "duct_rate_y": 0.5, "duct_mttr_h": 12.0, "diversity_premium": 0.15,
          "loss_per_min": 2_000.0, "sigma": 1.0}


def _circuit(key="nyse_ip_10g"):
    name, monthly, one_time, src = sm.CATALOGUE[key]
    return sm.Circuit(name, "10 Gb", monthly, one_time, ASSUME["mtbf_h"], ASSUME["mttr_h"], src, "2026-09-28")


def designs():
    c = _circuit()
    return [sm.Design("one circuit", (c,)),
            sm.Design("two circuits in one duct", (c, c), ASSUME["duct_rate_y"], ASSUME["duct_mttr_h"]),
            sm.Design("two diverse circuits", (c, c))]


def annual_cost(design):
    xc = sm.CATALOGUE["nyse_xc"][1]
    base = sum(12 * c.monthly + 12 * xc for c in design.circuits)
    return base * (1 + ASSUME["diversity_premium"]) if design.name == "two diverse circuits" else base


def results(years=2000):
    out = {}
    for d in designs():
        sims = [sm.simulate_year(d, seed=k, sigma=ASSUME["sigma"])["down_min"] for k in range(years)]
        a = sm.design_availability(d)
        out[d.name] = {"availability": a, "nines": sm.nines(a), "expected_min": sm.expected_down_min(d),
                       "sim_mean_min": float(np.mean(sims)), "sim_p95_min": float(np.percentile(sims, 95)),
                       "annual_cost": annual_cost(d), "loss": sm.expected_down_min(d) * ASSUME["loss_per_min"]}
    return out


def monthly_credits(design, schedule, seed=0, years=200):
    """Mean annual credit: each simulated year cut into twelve months, each month's uptime against the schedule,
    credit on the design's monthly charges."""
    monthly = sum(c.monthly for c in design.circuits)
    total = 0.0
    for k in range(years):
        sim = sm.simulate_year(design, seed=seed + k, sigma=ASSUME["sigma"])
        for m in sm.monthly_down_min(sim["intervals"]):
            total += sm.credit(sm.SCHEDULES[schedule], sm.uptime_pct(m, sm.HOURS_Y / 12 / 24), monthly)
    return total / years


def one_outage_credit(hours, schedule, monthly):
    return sm.credit(sm.SCHEDULES[schedule], sm.uptime_pct(60 * hours, 30), monthly)


def price_rows():
    return [(v[0], v[1], v[2], v[3]) for v in sm.CATALOGUE.values()]
