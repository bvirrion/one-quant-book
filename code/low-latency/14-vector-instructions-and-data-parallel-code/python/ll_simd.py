"""Chapter 14 -- the arithmetic of vector scans: cost per call and per byte from the measured scan, the break-even
message length, and bytes per nanosecond; the memory traffic of records against columns."""
import csv
import pathlib

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
FIG = ROOT / "figdata/low-latency/14-vector-instructions-and-data-parallel-code"


def read(name):
    with open(FIG / name, newline="", encoding="utf8") as f:
        return list(csv.DictReader(f))


def fit(method, lo=0, hi=10**9):
    """Least-squares line t = a + b L over the measured lengths in [lo, hi]: (a ns per call, b ns per byte)."""
    rows = [r for r in read("measured_scan.csv") if lo <= int(r["bytes"]) <= hi]
    L = np.array([int(r["bytes"]) for r in rows], float)
    t = np.array([float(r[method]) for r in rows])
    b, a = np.polyfit(L, t, 1)
    return float(a), float(b)


def per_byte(method):
    """Cost per byte of a method with no fixed cost (a line through the origin), least squares over every length."""
    rows = read("measured_scan.csv")
    L = np.array([int(r["bytes"]) for r in rows], float)
    t = np.array([float(r[method]) for r in rows])
    return float(L @ t / (L @ L))


def breakeven(method="avx2"):
    """Length above which the vector scan (a_v + b_v L, fitted where its full blocks run, L >= 32) is cheaper than a
    scalar loop charged per byte only (b_s L): L* = a_v / (b_s - b_v). Charging the scalar loop no fixed cost favours
    it, so the true break-even is lower still."""
    a_v, b_v = fit(method, 32)
    return a_v / (per_byte("scalar") - b_v)


def bytes_per_ns(method, L=4096):
    r = next(r for r in read("measured_scan.csv") if int(r["bytes"]) == L)
    return L / float(r[method])


def bytes_per_cycle(bpns, ghz):
    return bpns / ghz


def traffic(n, record_bytes=80, used_fields=5, field_bytes=8, out_bytes=8):
    """Bytes read and written to revalue n options stored as records or as columns."""
    return n * (record_bytes + out_bytes), n * (used_fields * field_bytes + out_bytes)


def lanes(vector_bytes, element_bytes):
    return vector_bytes // element_bytes


if __name__ == "__main__":
    for m in ("scalar", "sse2", "avx2"):
        print(m, fit(m), bytes_per_ns(m))
    print("break-even bytes", breakeven())
