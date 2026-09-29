"""Chapter 16 of One Quant Book 14: zones, round trips and costs in a public cloud (firm.cloudplan).

    ACCOUNTS                   two accounts' describe-availability-zones fixtures (documented shape, synthetic values)
    CASES                      round-trip models: same zone and cross zone fitted to a published measurement;
                               a shared host with noisy neighbours and a bare-metal host (labelled assumptions)
    percentiles(case)          simulated round-trip percentiles
    penalty_rows()             P(same name is same zone) and the expected round-trip penalty for n zones
    PLANS, plan_costs()        three monthly plans priced from the dated catalogue
"""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "cloudplan"))
import firm_cloudplan as cp  # noqa: E402

ACCOUNTS = {k: cp.load_zones(cp.DATA / f"describe_az_account_{k}.json") for k in ("a", "b")}
PUB = cp.RTT_PUBLISHED
CASES = {
    "same zone": cp.Rtt(PUB["same subnet"]["median"], PUB["same subnet"]["p99"], 0.0005, 1.5, 3.0),
    "cross zone": cp.Rtt(PUB["cross AZ"]["median"], PUB["cross AZ"]["p99"], 0.0003, 2.0, 4.0),
    "shared host, noisy neighbour": cp.Rtt(PUB["same subnet"]["median"], PUB["same subnet"]["p99"], 0.002, 5.0, 50.0),
}
QUANTILES = (50, 90, 99, 99.9, 99.99)
N_SAMPLES = 400_000
PLANS = {
    "four c7i.4xlarge in one zone": ([("c7i.4xlarge", 4)], 0.0),
    "four c7i.4xlarge over two zones": ([("c7i.4xlarge", 4)], 20_000.0),
    "two c7i.metal-24xl in one zone": ([("c7i.metal-24xl", 2)], 0.0),
}


def percentiles(case, n=N_SAMPLES, seed=1):
    x = cp.sample_rtt(CASES[case], n, seed)
    return {q: float(np.percentile(x, q)) for q in QUANTILES}


def penalty_rows(ns=(2, 3, 4, 6)):
    same, cross = PUB["same subnet"]["median"], PUB["cross AZ"]["median"]
    return [(n, cp.p_same_name_same_zone(n), cp.expected_penalty_us(n, same, cross)) for n in ns]


def plan_costs():
    cat = cp.load_catalogue()
    return {k: cp.monthly_cost(plan, cat, gb) for k, (plan, gb) in PLANS.items()}
