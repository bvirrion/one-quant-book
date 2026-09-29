"""Accelerators for quantitative work (One Quant Book 15, chapter 14).

Four reference kernels are timed on one core of this laptop (bench_roofline.py) and placed on the core's measured
roofline and on a data-centre graphics processor's roofline taken from its product page. Two workloads are then
predicted end to end with firm.roofline's model -- launch and synchronisation, host-device transfer, and the roof --
an overnight exposure Monte Carlo (10,000 paths, 120 dates, 5,000 trades) and an intraday request to price one trade;
the batch size at which the device breaks even on price requests follows. No accelerator is used.
"""
from __future__ import annotations

import csv
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/roofline"))
import firm_roofline as R  # noqa: E402

FIG = ROOT / "figdata/platforms/14-accelerators-for-quantitative-work"
DEV = R.DEVICES["H100 SXM (FP64)"]

# the chapter's workloads (stated assumptions, not measurements)
PATHS, DATES, TRADES, FACTORS = 10_000, 120, 5_000, 50
VALUE_FLOPS = 10.0                  # per (path, date, trade): a linear trade on one factor, discounted
TRADE_BYTES = 100.0                 # a trade's description sent to the device
REQUEST_FLOPS = 1.0e4               # pricing one trade intraday (100 cash flows on an interpolated curve)
REQUEST_BYTES = 1.0e3               # the trade and its result crossing the link
# a price request reads 0.8 bytes of curve and trade data per flop (intensity 1.25): memory-bound on both roofs
DEVICE_SHARE = 0.95                 # share of the overnight job's CPU time that moves to the device


def cpu_roof() -> R.Roof:
    rows = {r["quantity"]: float(r["value"]) for r in csv.DictReader(open(FIG / "measured_roof.csv"))}
    return R.Roof("one laptop core", rows["peak_flops"], rows["bandwidth"])


def kernels_measured() -> list[dict]:
    return [dict(r) for r in csv.DictReader(open(FIG / "measured_kernels.csv"))]


def exposure_job() -> list[R.Kernel]:
    n = PATHS * DATES * TRADES
    factors = PATHS * DATES * FACTORS
    paths = R.k_path(factors)
    value = R.Kernel("valuation", VALUE_FLOPS * n, 8.0 * (n + factors), TRADES * TRADE_BYTES)
    agg = R.k_exposure(PATHS, DATES, TRADES)
    return [paths, value, agg]


def overnight(cpu: R.Roof, dev: R.Roof = DEV) -> dict:
    ks = exposure_job()
    t_cpu = sum(cpu.time(k) for k in ks)
    moved = sum(k.transfer for k in ks) + DATES * 8.0            # trades in, the profile out
    t_dev = dev.launch * len(ks) + moved / dev.link + sum(dev.time(k) for k in ks)
    s = t_cpu / t_dev
    return {"cpu_s": t_cpu, "dev_s": t_dev, "speedup": s, "amdahl": R.amdahl(DEVICE_SHARE, s),
            "bytes": sum(k.bytes for k in ks), "flops": sum(k.flops for k in ks)}


def request(cpu: R.Roof, n: int = 1, dev: R.Roof = DEV) -> dict:
    k = R.Kernel("price request", REQUEST_FLOPS * n, 0.8 * REQUEST_FLOPS * n, REQUEST_BYTES * n)
    t_cpu, t_dev = cpu.time(k), dev.end_to_end(k)
    return {"n": n, "cpu_s": t_cpu, "dev_s": t_dev, "speedup": t_cpu / t_dev}


def break_even(cpu: R.Roof, dev: R.Roof = DEV) -> int | None:
    item = R.Kernel("price request", REQUEST_FLOPS, 0.8 * REQUEST_FLOPS, REQUEST_BYTES)
    return R.break_even(cpu, dev, item, 0.0)


def launch_sensitivity(cpu: R.Roof) -> list[tuple[float, int]]:
    out = []
    for launch in (1e-6, 5e-6, 10e-6, 50e-6):
        d = R.Roof(DEV.name, DEV.peak, DEV.bandwidth, DEV.link, launch)
        out.append((launch, break_even(cpu, d)))
    return out


def roofline_grid(cpu: R.Roof, dev: R.Roof = DEV) -> list[tuple[float, float, float]]:
    return [(float(i), cpu.attainable(i), dev.attainable(i)) for i in np.logspace(-2, 3, 61)]


def break_even_shared(cpu: R.Roof, shared: float = 1e6, dev: R.Roof = DEV) -> int | None:
    """Exercise 7: the break-even batch when `shared` bytes of market data cross with every request."""
    item = R.Kernel("price request", REQUEST_FLOPS, 0.8 * REQUEST_FLOPS, REQUEST_BYTES)
    return R.break_even(cpu, dev, item, shared)
