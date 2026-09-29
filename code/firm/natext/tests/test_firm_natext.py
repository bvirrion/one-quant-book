"""Acceptance tests of firm.natext (One Quant Book 15, chapter 9). The C++ and Rust builds are part of the test: a missing
toolchain fails it, it is never skipped."""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_natext as N


def data(n=10_000, seed=1):
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n)
    left = np.sort(rng.integers(0, 10**9, n)).astype(np.int64)
    right = np.sort(rng.integers(0, 10**9, n // 2)).astype(np.int64)
    return x, left, right


def test_four_ewmas_agree():
    x, _, _ = data()
    ref = N.ewma_python(x, 0.01)
    for f in (N.ewma_numpy, N.ewma_cpp, N.ewma_rust):
        assert np.max(np.abs(f(x, 0.01) - ref)) < 1e-12
    assert N.ewma_cpp(np.zeros(0), 0.1).size == 0 and N.ewma_rust(np.zeros(0), 0.1).size == 0


def test_four_asofs_agree_including_the_edges():
    _, left, right = data()
    left[0], left[-1] = -1, 2 * 10**9
    ref = N.asof_python(left, right)
    for f in (N.asof_numpy, N.asof_cpp, N.asof_rust):
        assert (f(left, right) == ref).all()
    assert ref[0] == -1 and ref[-1] == len(right) - 1


def test_steps_agree():
    for f in (N.step_python, N.step_cpp, N.step_rust):
        assert f(15.0, 20.0, 0.5) == 17.5


def test_zero_copy_into_the_callers_array():
    x, _, _ = data(1000)
    out = np.empty_like(x)
    before = out.ctypes.data
    N.ewma_cpp_into(x, 0.1, out)
    assert out.ctypes.data == before and np.allclose(out, N.ewma_numpy(x, 0.1))


def test_bindings_refuse_what_they_cannot_read_in_place():
    x, _, _ = data(1000)
    strided = x[::2]
    with pytest.raises(TypeError):
        N.ewma_cpp(strided, 0.1)                     # pybind11: c_style without forcecast, noconvert
    with pytest.raises(TypeError):
        N.ewma_cpp(x.astype(np.float32), 0.1)
    with pytest.raises(TypeError):
        N.ewma_rust(strided, 0.1)                    # ctypes: the wrapper's own check
    with pytest.raises(TypeError):
        N.asof_rust(np.arange(5, dtype=np.int32), np.arange(5, dtype=np.int64))
