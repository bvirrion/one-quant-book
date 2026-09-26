import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_lathist as lh
from make_lathist_fixture import PS, values

DATA = pathlib.Path(__file__).resolve().parents[1] / "data"


def test_index_is_monotone_and_ranges_tile_the_line():
    prev_hi = -1
    for i in range(0, lh.index_of(10**12) + 1):
        lo, hi = lh.bucket_range(i)
        assert lo == prev_hi + 1 and lh.index_of(lo) == i and lh.index_of(hi) == i
        prev_hi = hi


def test_relative_error_bound():
    for v in [300, 1_234, 99_999, 7_654_321, 2**40 + 12345]:
        lo, hi = lh.bucket_range(lh.index_of(v))
        assert (hi + 1 - lo) / v <= 2 ** -7


def test_quantiles_and_merge():
    h = lh.LatHist()
    for v in range(1, 101):
        h.record(v)
    assert (h.quantile(0.5), h.quantile(0.99), h.quantile(1.0), h.min, h.max) == (51, 100, 100, 1, 100)
    g = lh.LatHist()
    g.record(1000, n=100)
    h.merge(g)
    assert h.count == 200 and h.quantile(0.99) == 1000 and h.quantile(0.4) == 81


def test_coordinated_omission_correction():
    h = lh.LatHist()
    h.record_corrected(10_000, 1_000)   # one 10 us reply at a 1 us interval hides 8 more samples above the interval
    assert h.count == 9 and sorted(v for v in range(2000, 10_001, 1000)) == [2000, 3000, 4000, 5000, 6000, 7000, 8000,
                                                                            9000, 10000]


def test_fixture_is_current():
    h = lh.LatHist()
    for v in values():
        h.record(v)
    with open(DATA / "fixture_buckets.csv") as f:
        assert [(int(r["index"]), int(r["count"])) for r in csv.DictReader(f)] == h.nonzero()
    with open(DATA / "fixture_quantiles.csv") as f:
        assert [(float(r["p"]), int(r["value"])) for r in csv.DictReader(f)] == [(p, h.quantile(p)) for p in PS]
