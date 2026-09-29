"""Acceptance tests of firm.pyscale (One Quant Book 15, chapter 8)."""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_pyscale import chunks, ewma_kernel, probe, rolling_sum_kernel, run


def test_chunks_are_views_that_cover_the_array():
    a = np.arange(10)
    parts = list(chunks(a, 3))
    assert [len(p) for p in parts] == [3, 3, 3, 1] and np.concatenate(parts).tolist() == a.tolist()
    assert np.shares_memory(parts[1], a)


@pytest.mark.parametrize("size", [1, 2, 7, 1000, 5000])
def test_ewma_chunked_equals_whole(size):
    x = np.random.default_rng(1).standard_normal(5000)
    whole = ewma_kernel(0.05)(x, None)[0]
    y = np.empty_like(x)
    for i in range(len(x)):
        y[i] = x[0] if i == 0 else 0.95 * y[i - 1] + 0.05 * x[i]
    assert np.allclose(whole, y, atol=1e-12)
    assert np.allclose(run(chunks(x, size), ewma_kernel(0.05))[0], whole, atol=1e-12)


@pytest.mark.parametrize("size", [1, 3, 49, 50, 51, 4000])
def test_rolling_sum_chunked_equals_whole(size):
    x = np.random.default_rng(2).standard_normal(4000)
    c = np.concatenate([[0.0], np.cumsum(x)])
    i = np.arange(1, len(x) + 1)
    ref = c[i] - c[np.maximum(i - 50, 0)]
    assert np.max(np.abs(run(chunks(x, size), rolling_sum_kernel(50))[0] - ref)) < 1e-10


def test_probe_sees_the_allocation():
    _, _, small = probe(np.zeros, 1000)
    _, dt, big = probe(np.zeros, 1_000_000)
    assert big >= 8_000_000 > small and dt >= 0
