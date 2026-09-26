"""Numbers gate, Book 13 chapter 5."""
import csv
import pathlib
import sys
from decimal import ROUND_HALF_UP, Decimal

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import ll_measure as m  # noqa: E402

lh = sys.modules["firm_lathist"]
FIG = HERE.parents[2] / "figdata/low-latency/05-measuring-latency"


def r2(x):
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def test_histogram_arithmetic():
    assert lh.index_of(2**64 - 1) + 1 == 7424 and 2**-7 < 0.008
    assert round((3020 - 45) / 3.02, 1) == 985.1                                   # exercise 1
    assert lh.index_of(1000) == 506 and lh.bucket_range(506) == (1000, 1003)        # exercise 2
    assert lh.index_of(2**64 - 1, 10) + 1 == 28672 and round(100 * 2**-9, 3) == 0.195  # exercise 3
    h = lh.LatHist()
    h.record_corrected(9, 2)                                                        # exercise 4 (in ms)
    assert sorted(v for i, c in h.nonzero() for v in [lh.bucket_range(i)[0]] * c) == [3, 5, 7, 9]


def test_coordinated_omission():
    q, c = m.spectrum()
    assert c == {"closed loop": 99_000, "corrected": 99_900, "open loop": 100_000}
    p99 = {k: v[2] / 1000 for k, v in q.items()}
    assert (r2(p99["closed loop"]), r2(p99["corrected"]), r2(p99["open loop"])) == (0.16, 1.06, 1.87)
    assert all(abs(v[0] - 100.4) < 0.1 for v in q.values())                       # agree at the median
    assert len({round(v[3]) for v in q.values()}) == 1                             # and at p99.9
    assert round(100 * 100 / 99_000, 2) == 0.10
    q7, c7 = m.spectrum(stall=50_000, period=5e6)                                  # exercise 7
    assert c7["closed loop"] == 99_000
    assert (r2(q7["closed loop"][2] / 1000), r2(q7["corrected"][2] / 1000), r2(q7["open loop"][2] / 1000)) == (0.16, 1.07, 5.77)


def test_spectrum_caption():
    rows = list(csv.DictReader(open(FIG / "spectrum.csv")))
    ratio = {float(r["p"]): float(r["open_ms"]) / float(r["closed_ms"]) for r in rows}
    assert 10 <= ratio[0.99] < 15 and 40 < ratio[0.998] <= 50                     # ten to fifty


def test_measured_clocks():
    rows = {r["clock"]: float(r["ns_per_call"]) for r in csv.DictReader(open(FIG / "measured_clocks.csv"))}
    assert round(rows["rdtsc"], 1) == 6.5 and round(rows["rdtscp"]) == 11 and rows["rdtsc"] < rows["rdtscp"]
    kernel = [rows[k] for k in ("steady_clock", "CLOCK_MONOTONIC", "CLOCK_MONOTONIC_RAW", "CLOCK_REALTIME", "gettimeofday")]
    assert all(14 <= x <= 16 for x in kernel)
    rows_t = list(csv.DictReader(open(FIG / "measured_tsc.csv")))
    raw = [float(r["raw"]) for r in rows_t]
    mono = [float(r["monotonic"]) for r in rows_t]
    assert round(sum(raw) / len(raw), 4) == 2.9952 and (max(raw) - min(raw)) / min(raw) < 1e-5   # six digits
    assert round(sum(mono) / sum(raw) - 1, 2) == 0.02                                             # about 2% higher
    assert "clocksource: tsc" in (FIG / "measured_clocks.csv.meta").read_text()
