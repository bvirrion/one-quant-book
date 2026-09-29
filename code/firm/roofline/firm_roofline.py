"""firm.roofline -- rooflines, kernels and the end-to-end model of an accelerator (build of One Quant Book 15, ch. 14).

A kernel is described by the floating-point operations it performs, the bytes it moves between memory and the
processor, and the bytes it must move between host and device if it runs on an accelerator. A roof is a peak
arithmetic rate and a memory bandwidth (and, for a device, a host link and a per-request launch latency): the time a
kernel needs on it is at least max(flops / peak, bytes / bandwidth) (Williams, Waterman and Patterson's roofline), and
end to end on a device, launch + transfer / link + that. The CPU roof is measured on this machine, one core: the peak
by a large double-precision matrix product (numpy's BLAS, one thread), the bandwidth by a STREAM-style triad in
C++20 (cpp/firm_roofline_triad.cpp). Device roofs are data with their sources. No accelerator is used or required.

Flop counting convention: additions, multiplications and fused multiply-adds count 1 (an FMA 2); a call to exp counts 1,
although it costs many cycles -- a kernel dominated by transcendental functions sits below the roof for that reason.

API (stable):
    Kernel(name, flops, bytes, transfer=0.0)      .intensity (flops per byte)
    Roof(name, peak, bandwidth, link=inf, launch=0.0, source='')
        .attainable(intensity) -> flop/s ; .time(kernel) -> s ; .end_to_end(kernel) -> s ; .ridge -> flops per byte
    DEVICES {name: Roof}                           cited device figures (dated in the chapter)
    measure_peak(n=2000, reps=3) -> flop/s ; measure_bandwidth(n=2**24, reps=10) -> byte/s   (one core)
    path_step(S, Z, a, b), basket_payoff(S, w, K), exposure_profile(V), matmul(A, B)      reference kernels (numpy)
    k_path(n), k_basket(paths, assets), k_exposure(paths, dates, trades), k_matmul(n)      their descriptors
    amdahl(parallel_share, speedup) -> overall speed-up
    break_even(cpu, dev, per_item, shared) -> smallest batch n with dev.end_to_end < cpu.time for n items
"""
from __future__ import annotations

import math
import os
import pathlib
import sys
import time
from dataclasses import dataclass

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ubench"))


@dataclass(frozen=True)
class Kernel:
    name: str
    flops: float
    bytes: float
    transfer: float = 0.0             # host <-> device bytes if offloaded

    @property
    def intensity(self) -> float:
        return self.flops / self.bytes

    def times(self, k: float) -> Kernel:
        return Kernel(self.name, self.flops * k, self.bytes * k, self.transfer * k)


@dataclass(frozen=True)
class Roof:
    name: str
    peak: float                       # flop/s
    bandwidth: float                  # byte/s
    link: float = math.inf            # host link, byte/s
    launch: float = 0.0               # s per request (launch and synchronisation)
    source: str = ""

    @property
    def ridge(self) -> float:
        return self.peak / self.bandwidth

    def attainable(self, intensity: float) -> float:
        return min(self.peak, intensity * self.bandwidth)

    def time(self, k: Kernel) -> float:
        return max(k.flops / self.peak, k.bytes / self.bandwidth)

    def end_to_end(self, k: Kernel) -> float:
        return self.launch + k.transfer / self.link + self.time(k)


LAUNCH = 10e-6                        # an assumption of the chapter, not a datasheet figure (see its sensitivity)
DEVICES = {
    "H100 SXM (FP64)": Roof("H100 SXM (FP64)", 34e12, 3.35e12, link=128e9, launch=LAUNCH,
                            source="NVIDIA H100 product page: FP64 34 TFLOPS, 3.35 TB/s, PCIe Gen5 128 GB/s"),
    "H100 SXM (FP64 tensor)": Roof("H100 SXM (FP64 tensor)", 67e12, 3.35e12, link=128e9, launch=LAUNCH,
                                   source="NVIDIA H100 product page: FP64 Tensor Core 67 TFLOPS"),
}


# ------------------------------------------------------------ measuring one core
def measure_peak(n: int = 2000, reps: int = 3) -> float:
    """Double-precision flop/s of a large matrix product on one BLAS thread (set the thread variables first)."""
    rng = np.random.default_rng(0)
    a, b = rng.standard_normal((n, n)), rng.standard_normal((n, n))
    best = math.inf
    for _ in range(reps):
        t = time.perf_counter()
        a @ b
        best = min(best, time.perf_counter() - t)
    return 2.0 * n ** 3 / best


def measure_bandwidth(n: int = 2 ** 24, reps: int = 10) -> float:
    import firm_ubench as u
    exe = u.compile_cpp(HERE / "cpp" / "firm_roofline_triad.cpp", flags=("-std=c++20", "-O2", "-march=native",
                                                                           "-Wall", "-Wextra", "-Werror"))
    return float(u.run(exe, n, reps).split()[0]) * 1e9


def one_thread() -> bool:
    return all(os.environ.get(v) == "1" for v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS"))


# ------------------------------------------------------------ reference kernels and their descriptors
def path_step(S: np.ndarray, Z: np.ndarray, a: float, b: float) -> np.ndarray:
    """One log-Euler step of geometric Brownian motion, in place: S *= exp(a + b Z)."""
    S *= np.exp(a + b * Z)
    return S


def k_path(n: int) -> Kernel:
    return Kernel("path step", 4.0 * n, 24.0 * n)            # mul, add, exp, mul; read Z and S, write S


def basket_payoff(S: np.ndarray, w: np.ndarray, K: float) -> np.ndarray:
    return np.maximum(S @ w - K, 0.0)


def k_basket(paths: int, assets: int) -> Kernel:
    return Kernel("basket payoff", paths * (2.0 * assets + 2.0), 8.0 * paths * (assets + 1))


def exposure_profile(V: np.ndarray) -> np.ndarray:
    """V (paths, dates, trades) of trade values: the expected positive exposure of the netting set by date."""
    return np.maximum(V.sum(axis=2), 0.0).mean(axis=0)


def k_exposure(paths: int, dates: int, trades: int) -> Kernel:
    n = paths * dates * trades
    return Kernel("exposure aggregation", n + 2.0 * paths * dates, 8.0 * n)


def matmul(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    return A @ B


def k_matmul(n: int) -> Kernel:
    return Kernel("matrix product", 2.0 * n ** 3, 3 * 8.0 * n ** 2)


# ------------------------------------------------------------ end-to-end decisions
def amdahl(parallel_share: float, speedup: float) -> float:
    return 1.0 / ((1.0 - parallel_share) + parallel_share / speedup)


def break_even(cpu: Roof, dev: Roof, per_item: Kernel, shared: float, n_max: int = 10 ** 9) -> int | None:
    """Smallest batch n for which the device, end to end, beats the CPU on n items that share `shared` bytes of
    transfer (market data sent once) besides each item's own transfer."""
    def gain(n):
        k = per_item.times(n)
        return cpu.time(k) - dev.end_to_end(Kernel(k.name, k.flops, k.bytes, k.transfer + shared))

    if gain(n_max) <= 0:
        return None
    lo, hi = 1, n_max
    if gain(lo) > 0:
        return 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (mid, hi) if gain(mid) <= 0 else (lo, mid)
    return hi
