"""Acceptance tests of firm.roofline (One Quant Book 15, chapter 14)."""
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_roofline as R  # noqa: E402


def test_roof_arithmetic():
    r = R.Roof("x", 100e9, 20e9, link=10e9, launch=1e-5)
    assert r.ridge == 5.0 and r.attainable(1.0) == 20e9 and r.attainable(50.0) == 100e9
    k = R.Kernel("k", 1e9, 1e9, transfer=1e8)
    assert k.intensity == 1.0 and r.time(k) == pytest.approx(0.05) and r.end_to_end(k) == pytest.approx(0.06001)
    assert k.times(2).flops == 2e9 and R.Roof("c", 1e9, 1e9).end_to_end(k) == 1.0


def test_kernels_compute_what_they_say():
    rng = np.random.default_rng(1)
    S, Z = np.ones(5), rng.standard_normal(5)
    assert np.allclose(R.path_step(S.copy(), Z, 0.01, 0.2), np.exp(0.01 + 0.2 * Z))
    B = rng.lognormal(0, 0.2, (100, 4))
    w = np.full(4, 0.25)
    assert np.allclose(R.basket_payoff(B, w, 1.0), [max(sum(r) / 4 - 1.0, 0.0) for r in B])
    V = rng.standard_normal((30, 3, 7))
    ref = [np.mean([max(V[p, d].sum(), 0.0) for p in range(30)]) for d in range(3)]
    assert np.allclose(R.exposure_profile(V), ref)
    A = rng.standard_normal((3, 3))
    assert np.allclose(R.matmul(A, np.eye(3)), A)
    assert R.k_matmul(1000).intensity == pytest.approx(1000 / 12)
    assert R.k_path(10).intensity == pytest.approx(1 / 6) and R.k_basket(10, 20).intensity == pytest.approx(42 / 168)


def test_amdahl_and_break_even():
    assert R.amdahl(0.95, 1e12) == pytest.approx(20.0) and R.amdahl(0.0, 100) == 1.0
    cpu = R.Roof("cpu", 1e9, 1e12)
    dev = R.Roof("dev", 1e12, 1e12, link=math.inf, launch=1e-3)
    item = R.Kernel("i", 1e5, 1.0)                                     # 100 us on the CPU, negligible on the device
    assert R.break_even(cpu, dev, item, 0.0) == 11                     # 11 x 100 us > 1 ms + 11 x 0.1 us
    slow_link = R.Roof("dev", 1e12, 1e12, link=1e3, launch=0.0)
    assert R.break_even(cpu, slow_link, R.Kernel("i", 1e5, 1.0, transfer=1e3), 0.0) is None


def test_device_data_and_triad():
    d = R.DEVICES["H100 SXM (FP64)"]
    assert (d.peak, d.bandwidth, d.link) == (34e12, 3.35e12, 128e9) and "product page" in d.source
    bw = R.measure_bandwidth(n=1 << 18, reps=3)
    assert 1e9 < bw < 1e12
