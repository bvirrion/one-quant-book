"""firm.payband -- public pay scales as annual ranges (build of One Quant Book 17, chapter 9).

A public employer publishes its pay as grades, each a band from a minimum to a maximum of basic pay, and a locality
supplement per duty station applied to basic pay, subject to an overall cap. A position's pay range at a station is
the grade's band times (1 + locality rate), each end capped. The module converts published scales to annual ranges and
compares a band with another source's range (the fraction of the other range the band covers).

API (stable):
    Band(grade, lo, hi) ; Scale(name, bands, locality, cap)
    load_scale(name, bands_csv, locality_csv, cap) -> Scale
    at(scale, grade, station) -> (lo, hi) with locality applied and capped
    overlap(a, b) -> share of range b covered by range a
"""
import csv
from dataclasses import dataclass


@dataclass(frozen=True)
class Band:
    grade: str
    lo: float
    hi: float


@dataclass(frozen=True)
class Scale:
    name: str
    bands: dict
    locality: dict
    cap: float | None = None


def load_scale(name, bands_csv, locality_csv, cap=None):
    with open(bands_csv) as f:
        bands = {r["grade"]: Band(r["grade"], float(r["min"]), float(r["max"])) for r in csv.DictReader(f)}
    with open(locality_csv) as f:
        loc = {r["station"]: float(r["rate_pct"]) / 100 for r in csv.DictReader(f)}
    return Scale(name, bands, loc, cap)


def at(scale, grade, station):
    b = scale.bands[str(grade)]
    k = 1 + scale.locality[station]
    lo, hi = b.lo * k, b.hi * k
    if scale.cap is not None:
        lo, hi = min(lo, scale.cap), min(hi, scale.cap)
    return lo, hi


def overlap(a, b):
    lo, hi = max(a[0], b[0]), min(a[1], b[1])
    return max(hi - lo, 0.0) / (b[1] - b[0])
