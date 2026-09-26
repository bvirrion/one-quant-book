"""Chapter 8 of One Quant Book 13: readers of the measured flag matrices, and the exact float sum."""
import csv
import math
import pathlib

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/low-latency/08-cpp-for-latency-iii-the-compiler"


def rows(name):
    with open(FIG / name, newline="") as f:
        return {r["name"]: r for r in csv.DictReader(f)}


def harmonic(n):
    return math.fsum(1.0 / k for k in range(1, n + 1))
