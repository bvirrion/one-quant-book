"""firm.natext -- one kernel, four implementations, and the bindings between them (build of One Quant Book 15, ch. 9).

The kernels (an exponentially weighted average; an as-of lookup of sorted times) exist in pure Python, numpy, C++20
bound with pybind11 (cpp/firm_natext_py.cpp, built here with g++ and python3-config) and in Rust behind a C ABI
(rust/, a cdylib with no external crates, loaded with ctypes). The C++ binding takes numpy arrays through the buffer
protocol without copying and refuses arrays that are not C-contiguous float64 (or int64), releasing the interpreter
lock while it computes; the ctypes wrapper checks the same things itself, because ctypes checks nothing.

API (stable):
    ewma_python(x, alpha), ewma_numpy(x, alpha), ewma_cpp(x, alpha), ewma_rust(x, alpha) -> np.ndarray[float64]
    ewma_cpp_into(x, alpha, out)                     writes into the caller's array
    asof_python(left, right), asof_numpy(left, right), asof_cpp(left, right), asof_rust(left, right)
        -> np.ndarray[int64]: for each left time, the index of the last right time at or before it, -1 if none
    step_cpp(y, x, alpha), step_rust(y, x, alpha), step_python(y, x, alpha) -> float   one step, per call
    cpp_module() -> the compiled pybind11 module (built on first use); rust_library() -> ctypes.CDLL (built once)
"""
from __future__ import annotations

import ctypes
import functools
import importlib
import pathlib
import subprocess
import sys
import sysconfig

import numpy as np
from scipy.signal import lfilter

HERE = pathlib.Path(__file__).resolve().parent
BIN = HERE / "cpp" / "bin"


# ------------------------------------------------------------------------------------------- pure Python and numpy
def ewma_python(x, alpha: float) -> np.ndarray:
    out, y = [], None
    for v in x:
        y = v if y is None else (1.0 - alpha) * y + alpha * v
        out.append(y)
    return np.array(out, dtype=float)


def ewma_numpy(x, alpha: float) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    if len(x) == 0:
        return x.copy()
    y, _ = lfilter([alpha], [1.0, -(1.0 - alpha)], x, zi=[(1.0 - alpha) * x[0]])
    return y


def asof_python(left, right) -> np.ndarray:
    out, j = [], 0
    for t in left:
        while j < len(right) and right[j] <= t:
            j += 1
        out.append(j - 1)
    return np.array(out, dtype=np.int64)


def asof_numpy(left, right) -> np.ndarray:
    return np.searchsorted(right, left, side="right").astype(np.int64) - 1


def step_python(y: float, x: float, alpha: float) -> float:
    return (1.0 - alpha) * y + alpha * x


# ------------------------------------------------------------------------------------------- C++ (pybind11)
@functools.lru_cache(maxsize=1)
def cpp_module():
    import pybind11
    BIN.mkdir(parents=True, exist_ok=True)
    target = BIN / ("natext_cpp" + sysconfig.get_config_var("EXT_SUFFIX"))
    src = HERE / "cpp" / "firm_natext_py.cpp"
    if not target.exists() or target.stat().st_mtime < max(src.stat().st_mtime,
                                                            (HERE / "cpp" / "firm_natext.hpp").stat().st_mtime):
        # The running interpreter's own headers (python3-config on PATH may belong to another Python).
        includes = ["-I" + sysconfig.get_paths()["include"]]
        subprocess.run(["g++", "-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror", "-shared", "-fPIC", *includes,
                        f"-I{pybind11.get_include()}", str(src), "-o", str(target)], check=True)
    sys.path.insert(0, str(BIN))
    return importlib.import_module("natext_cpp")


def ewma_cpp(x, alpha: float) -> np.ndarray:
    return cpp_module().ewma(x, alpha)


def ewma_cpp_into(x, alpha: float, out) -> None:
    cpp_module().ewma_into(x, alpha, out)


def asof_cpp(left, right) -> np.ndarray:
    return cpp_module().asof_index(left, right)


def step_cpp(y: float, x: float, alpha: float) -> float:
    return cpp_module().ewma_step(y, x, alpha)


# ------------------------------------------------------------------------------------------- Rust (C ABI, ctypes)
_D, _I = ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_int64)


@functools.lru_cache(maxsize=1)
def rust_library() -> ctypes.CDLL:
    crate = HERE / "rust"
    subprocess.run(["cargo", "build", "--release", "-q"], cwd=crate, check=True)
    lib = ctypes.CDLL(str(crate / "target" / "release" / "libnatext_rs.so"))
    lib.natext_ewma.argtypes = [_D, ctypes.c_size_t, ctypes.c_double, _D]
    lib.natext_ewma.restype = None
    lib.natext_asof.argtypes = [_I, ctypes.c_size_t, _I, ctypes.c_size_t, _I]
    lib.natext_asof.restype = None
    lib.natext_ewma_step.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double]
    lib.natext_ewma_step.restype = ctypes.c_double
    return lib


def _check(a, dtype):
    """ctypes passes a pointer and trusts it: the wrapper must check what the C++ binding
    checks for us."""
    if not isinstance(a, np.ndarray) or a.dtype != dtype or not a.flags.c_contiguous:
        raise TypeError(f"need a C-contiguous numpy array of {np.dtype(dtype)}")
    return a


def ewma_rust(x, alpha: float) -> np.ndarray:
    x = _check(x, np.float64)
    out = np.empty_like(x)
    rust_library().natext_ewma(x.ctypes.data_as(_D), len(x), alpha, out.ctypes.data_as(_D))
    return out


def asof_rust(left, right) -> np.ndarray:
    left, right = _check(left, np.int64), _check(right, np.int64)
    out = np.empty(len(left), dtype=np.int64)
    rust_library().natext_asof(left.ctypes.data_as(_I), len(left), right.ctypes.data_as(_I), len(right),
                               out.ctypes.data_as(_I))
    return out


def step_rust(y: float, x: float, alpha: float) -> float:
    return rust_library().natext_ewma_step(y, x, alpha)
