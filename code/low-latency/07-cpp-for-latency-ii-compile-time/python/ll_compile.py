"""Chapter 7 of One Quant Book 13: readers of the measured dispatch CSV and the arithmetic of the chapter's problem."""
import csv
import pathlib

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/low-latency/07-cpp-for-latency-ii-compile-time"


def dispatch():
    with open(FIG / "measured_dispatch.csv", newline="") as f:
        return {r["design"]: (float(r["one_type"]), float(r["mixed"])) for r in csv.DictReader(f)}


def pow10(n):
    t = [1]
    for _ in range(n):
        t.append(t[-1] * 10)
    return t
