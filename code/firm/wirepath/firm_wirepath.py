"""firm.wirepath -- Book 13's tick-to-trade path with the wire added (build of One Quant Book 14, chapter 5).

One Quant Book 13 (chapter 26, firm.ticktotrade) measured the software stages of the firm's trading path on a laptop,
from a packet's arrival in the feed thread to the order's hand-off to the kernel. A wire-to-wire budget adds what
lies outside the program: the cage's network from the venue's handoff to the card (firm.cagenet), the card's
receive path into memory, the card's transmit path, and the network back to the order handoff. This module composes
them with firm.latbudget, stage by stage, into a distribution of wire-to-wire latency.

Stages are lognormal, fitted to a median and a 99th percentile (sigma = ln(p99/p50) / 2.326); constants are
stages with p99 = p50. Book 13's measured medians and 99th percentiles are read (read-only) from
figdata/low-latency/26-build-tick-to-trade-measured/measured_stages.csv; the card's stages are model values stated
by the caller. The 99.9th percentiles of the laptop measurement (scheduler preemptions) are not modelled.

API (stable):
    Stage(name, p50_ns, p99_ns, kind)                      kind: "wire" | "card" | "software" | "hardware"
    book13_software(stages=SOFTWARE) -> [Stage]            from Book 13's measured CSV
    wire_stages(cage, feed_path, order_path, feed_frame, order_frame, gbps) -> [Stage]   from a firm.cagenet Cage
    card_stages(rx_p50, rx_p99, tx_p50, tx_p99) -> [Stage]
    hardware_stage(cycles, clock_mhz) -> Stage                                          a fixed hardware decision
    compose(stages, n, seed) -> dict(total, per_stage)     independent draws, summed with firm.latbudget
    report(stages, n, seed) -> list[dict(stage, kind, p50, p99)]  plus a 'wire-to-wire' row
"""
import csv
import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

FIRM = pathlib.Path(__file__).resolve().parents[1]
ROOT = FIRM.parents[1]
sys.path.insert(0, str(FIRM / "latbudget"))
import firm_latbudget as lb  # noqa: E402

BOOK13 = ROOT / "figdata" / "low-latency" / "26-build-tick-to-trade-measured" / "measured_stages.csv"
SOFTWARE = ("decode", "ring", "book", "strategy", "risk", "gateway")
Z99 = 2.3263478740408408


@dataclass(frozen=True)
class Stage:
    name: str
    p50_ns: float
    p99_ns: float
    kind: str = "software"

    def sample(self, rng, n):
        if self.p99_ns <= self.p50_ns:
            return np.full(n, float(self.p50_ns))
        sigma = math.log(self.p99_ns / self.p50_ns) / Z99
        return self.p50_ns * np.exp(sigma * rng.standard_normal(n))


def book13_software(stages=SOFTWARE):
    rows = {r["stage"]: r for r in csv.DictReader(open(BOOK13))}
    return [Stage(s, float(rows[s]["p50_ns"]), float(rows[s]["p99_ns"]), "software") for s in stages]


def wire_stages(cage, feed_path, order_path, feed_frame=104, order_frame=100, gbps=10.0):
    return [Stage("network in", cage.latency_ns(feed_path, feed_frame, gbps), 0, "wire"),
            Stage("network out", cage.latency_ns(order_path, order_frame, gbps), 0, "wire")]


def card_stages(rx_p50, rx_p99, tx_p50, tx_p99):
    return [Stage("card receive", rx_p50, rx_p99, "card"), Stage("card transmit", tx_p50, tx_p99, "card")]


def hardware_stage(cycles, clock_mhz):
    t = cycles * 1000.0 / clock_mhz
    return Stage("hardware decision", t, t, "hardware")


def compose(stages, n=100_000, seed=1):
    rng = np.random.default_rng(seed)
    per = {s.name: s.sample(rng, n) for s in stages}
    total = lb.compose_joint(per)                   # the draws are independent, aligned by index
    return {"total": total, "per_stage": per}


def report(stages, n=100_000, seed=1):
    c = compose(stages, n, seed)
    rows = [{"stage": s.name, "kind": s.kind, "p50": lb.quantile(c["per_stage"][s.name], 0.5),
             "p99": lb.quantile(c["per_stage"][s.name], 0.99)} for s in stages]
    rows.append({"stage": "wire-to-wire", "kind": "total", "p50": lb.quantile(c["total"], 0.5),
                 "p99": lb.quantile(c["total"], 0.99)})
    return rows
