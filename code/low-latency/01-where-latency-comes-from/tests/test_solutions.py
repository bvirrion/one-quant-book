"""Numbers gate: every number printed in Book 13, chapter 1 (text and solutions)."""
import csv
import math
import pathlib
import sys

from scipy.stats import norm

HERE = pathlib.Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE / "python"))
import ll_budget as b  # noqa: E402

FIG = ROOT / "figdata/low-latency/01-where-latency-comes-from"


def test_physics():
    assert round(b.fibre_ns_per_m(), 2) == 4.88 and round(30 * b.fibre_ns_per_m()) == 146
    assert b.serialisation_ns(64, 10) == 67.2 and round(b.serialisation_ns(64, 25), 1) == 26.9
    assert round(45 * b.fibre_ns_per_m(1.462)) == 219                                   # exercise 1
    assert b.serialisation_ns(128, 10) == 118.4 and round(b.serialisation_ns(128, 25), 1) == 47.4  # exercise 2


def test_composition():
    c = b.composition()
    assert (round(c["sum_p50"] / 1000, 2), round(c["p50"] / 1000, 2), round(c["mean"] / 1000, 2)) == (2.13, 2.17, 2.32)
    assert abs(c["mean"] - c["mean_sum"]) < 1e-6
    assert (round(c["p99"] / 1000, 2), round(c["sum_p99"] / 1000, 2), round(c["sum_union"] / 1000, 1)) == (6.56, 3.59, 28.7)
    assert round(100 * c["level"], 2) == 99.83 and round(100 * (1 - 0.997 ** 6), 1) == 1.8
    assert round(c["sum_union"] / c["p99"]) == 4
    assert round(100 * (1 - 0.991 ** 2), 2) == 1.79                                     # example, two stages
    e = b.composition(stall_p=0.05)                                                     # exercise 7
    assert (round(e["sum_p99"] / 1000), round(e["p99"] / 1000)) == (79, 32)


def test_race():
    r = b.race_results()
    assert round(r["base"][0], 3) == 0.661 and round(r["half_median"][0], 3) == 0.980
    assert round(r["half_stalls"][0], 3) == 0.667 and round(r["no_stalls"][0], 3) == 0.674
    assert (round(r["base"][1] / 1000, 2), round(r["base"][2] / 1000, 1), round(r["half_stalls"][2] / 1000, 1)) == (2.01, 23.6, 3.5)
    closed = norm.cdf(math.log(2.2 / 2.0) / (0.15 * math.sqrt(2)))                      # problem 2
    assert round(closed, 3) == 0.673
    rows = [(float(x["median_us"]), float(x["with_stalls"]), float(x["no_stalls"])) for x in csv.DictReader(open(FIG / "race.csv"))]
    at2 = [r for r in rows if r[0] == 2.0][0]
    gain = at2[2] - at2[1]
    assert round(gain, 3) == 0.013                                                      # exercise 6
    (m0, p0, _), (m1, p1, _) = [r for r in rows if r[0] in (1.95, 2.0)]
    m_eq = m1 - (at2[2] - p1) / ((p0 - p1) / (m1 - m0))
    assert round((2.0 - m_eq) * 1000) == 16
    slope = (p0 - p1) / (m1 - m0)
    assert round(slope, 2) == 0.81 and round(100 * slope * 0.1) == 8                    # caption: a tenth of a us, 8 points
    (a0, q0, _), (a1, q1, _) = [r for r in rows if r[0] in (1.6, 1.65)]
    m90 = a0 + (q0 - 0.9) / (q0 - q1) * (a1 - a0)                                       # problem 13
    assert round(m90, 2) == 1.64 and round((m90 - 1.0) / 5 * 1000) == 128


def test_exposure_and_exercises():
    stale = 100_000 * 0.02 * 30e-6                                                       # problem 9: 2,000 stalls/s x 30 us
    assert round(stale, 2) == 0.06
    per_day = 20 * stale * 0.5 * 0.01 * 100 * 6.5 * 3600                                # problem 10
    assert round(per_day) == 14040 and round(per_day / 2) == 7020
    assert 300 + 80 + 150 + 500 == 1030                                                 # exercise 3
    assert round(100 * (1 - 0.996 ** 5), 2) == 1.98                                     # exercise 4
    assert 1 - 0.001 / 4 == 0.99975 and 1 - 0.01 / 5 == 0.998                           # exercise 5, problem 15


def test_measured_claims():
    """Claims made in prose about the measured chart, checked against the committed CSV with wide margins."""
    rows = {r["stage"]: r for r in csv.DictReader(open(FIG / "measured_path.csv"))}
    stages = ("decode", "book", "decide", "encode")
    assert max(stages, key=lambda s: float(rows[s]["p50"])) == "book"
    assert 40 < float(rows["book"]["p50"]) < 160
    assert all(float(rows[s]["p999"]) > 1.5 * float(rows[s]["p99"]) for s in ("decode", "book", "decide"))
    assert float(rows["total"]["max"]) > 100 * float(rows["total"]["p50"])
    assert 500 < float(rows["book"]["p999"]) < 2500
    meta = (FIG / "measured_path.csv.meta").read_text()
    assert "cpus: 2" in meta and "passes: 200" in meta
