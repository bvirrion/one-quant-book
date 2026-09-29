"""firm.powerlink -- intraday power and betting-exchange connectivity (build of One Quant Book 14, chapter 26).

Cross-border intraday power: orders from each country reach a shared order book through their local trading system;
when two orders match across a border, the capacity they need is allocated with the match, first come, first served,
so when capacity is scarce it goes to the first orders to arrive. Participants' latencies to the shared book are
lognormal with stated medians and spreads (assumptions); results are a labelled simulation. The gate-closure clock
gives the time left for cross-zonal trading. Betting exchange: requests for market data are limited by a published
weight per market and projection (data/betfair_weights.csv, dated rows), so polling many markets costs many requests;
transactions above an hourly threshold are charged (the threshold is a dated parameter, the charge an input).

API (stable):
    Participant(name, median_ms, sigma=0.3)
    capacity_race(participants, slots=1, n=40000, seed=0) -> {name: share of events in which it got capacity}
    gate_closure(delivery_min, gct_min=60) -> the last minute of cross-zonal trading for a delivery period
    load_weights(path) ; markets_per_request(weight, limit=200) ; poll_requests_per_s(markets, weight, hz)
    poll_staleness_ms(hz, rtt_ms) -> mean age of polled data ; charged_transactions(per_hour, threshold=5000)
"""
import csv
import math
import pathlib
from dataclasses import dataclass

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent


@dataclass(frozen=True)
class Participant:
    name: str
    median_ms: float
    sigma: float = 0.3


def capacity_race(participants, slots=1, n=40000, seed=0):
    """Each event: every participant sends one order; the first `slots` arrivals get the scarce capacity."""
    rng = np.random.default_rng(seed)
    t = np.column_stack([p.median_ms * np.exp(p.sigma * rng.standard_normal(n)) for p in participants])
    rank = np.argsort(np.argsort(t, axis=1), axis=1)
    got = rank < slots
    return {p.name: float(got[:, i].mean()) for i, p in enumerate(participants)}


def gate_closure(delivery_min, gct_min=60):
    return delivery_min - gct_min


def load_weights(path=HERE / "data" / "betfair_weights.csv"):
    with open(path) as f:
        return {r["projection"]: int(r["weight"]) for r in csv.DictReader(f)}


def markets_per_request(weight, limit=200):
    return limit // weight


def poll_requests_per_s(markets, weight, hz, limit=200):
    return math.ceil(markets / markets_per_request(weight, limit)) * hz


def poll_staleness_ms(hz, rtt_ms):
    """Polling every 1/hz seconds: on average half an interval old, plus the request's round trip."""
    return 1000.0 / (2 * hz) + rtt_ms


def charged_transactions(per_hour, threshold=5000):
    return max(0, per_hour - threshold)
