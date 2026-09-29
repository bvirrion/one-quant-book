"""One Quant Book 17, chapter 25: leadership roles -- accountability and a new partner's economics.

Accountability: firm.roles.SMF_TIERS (the FCA's guide for solo-regulated firms, July 2019 update; ledger F1). The
partner: firm.roles.partner_path on Book 16's firm.partnership with ILLUSTRATIVE terms (no firm publishes its points or
retention rules): firm profit, partners, points, contribution, payout ratio and admissions below; the salaried
alternative is an illustrative head of desk. Pay context: chapter 14's EBA table (management body) and the survey's
chief executives and financial managers (oews_roles.csv).
"""
import csv
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/roles"))
import firm_roles as fr  # noqa: E402

DATA = ROOT / "data/industry"
MEAN, SD = 300.0, 200.0           # firm profit a year, $ million (illustrative)
PARTNERS, POINTS = 30, 100
NEW_POINTS, CONTRIBUTION = 30, 1.0
PAYOUT = 0.6
ADMIT_YEAR, ADMIT = 3, 3
YEARS, N, SEED = 5, 20_000, 25
ALTERNATIVE = 1.2                 # salaried head of desk, $ million a year (illustrative)


def run(new_points=NEW_POINTS, n=N, seed=SEED, **kw):
    p = dict(mean=MEAN, sd=SD, partners=PARTNERS, points=POINTS, contribution=CONTRIBUTION, payout=PAYOUT,
             admit_year=ADMIT_YEAR, admit=ADMIT, years=YEARS)
    p.update(kw)
    return fr.partner_path(new_points=new_points, n=n, rng=np.random.default_rng(seed), **p)


def summary(d):
    inc, cap = d["draws"].sum(1), d["capital"]
    return {"income": float(inc.mean()), "income_p10": float(np.percentile(inc, 10)),
            "income_p90": float(np.percentile(inc, 90)), "capital5": float(cap[:, -1].mean()),
            "capital5_p05": float(np.percentile(cap[:, -1], 5)), "below": float((cap < CONTRIBUTION).any(1).mean()),
            "by_year_draw": d["draws"].mean(0).tolist(), "by_year_cap": cap.mean(0).tolist(),
            "by_year_cap_p05": np.percentile(cap, 5, axis=0).tolist()}


def break_even(n=N, lo=1.0, hi=60.0, tol=0.01):
    """Points at which the expected five-year draws equal the salaried alternative (bisection, same paths)."""
    target = YEARS * ALTERNATIVE
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if run(mid, n)["draws"].sum(1).mean() < target:
            lo = mid
        else:
            hi = mid
    pts = 0.5 * (lo + hi)
    return pts, pts / (PARTNERS * POINTS + pts)


def eba_mb():
    with open(DATA / "eba_high_earners.csv") as f:
        return {(r["institutions"], r["business_area"]): r for r in csv.DictReader(f)
                if r["business_area"].startswith("MB") and r["high_earners"] not in ("0", "")}


def survey(naics="523000"):
    with open(DATA / "oews_roles.csv") as f:
        return {r["occ"]: r for r in csv.DictReader(f) if r["naics"] == naics
                and r["occ"] in ("11-1011", "11-1021", "11-3021", "11-3031")}


if __name__ == "__main__":
    s = summary(run())
    print({k: (round(v, 3) if isinstance(v, float) else [round(x, 3) for x in v]) for k, v in s.items()})
    print(break_even(n=4000))
    print({k: fr.smf_count(k) for k in fr.SMF_TIERS})
    for k, v in eba_mb().items():
        print(k, v["high_earners"], v["avg_total_eur"], v["variable_to_fixed"])
    for k, v in survey().items():
        print(k, v["occupation"], v["employment"], v["p10"], v["p50"], v["p90"])
