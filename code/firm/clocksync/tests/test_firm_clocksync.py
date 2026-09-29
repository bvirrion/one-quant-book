import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_clocksync as cs  # noqa: E402


class Zero:
    """A generator that draws zeros: an exchange without queueing or timestamp noise."""

    def exponential(self, scale, n):
        return np.zeros(n)

    def normal(self, mu, sd, n):
        return np.zeros(n)


def test_two_way_formula_and_asymmetry():
    p = cs.Path(base_ns=2000, asym_ns=0, queue_ns=0, stamp_ns=0)
    est, rtt = cs.exchange(Zero(), 12_345.0, p, False)
    assert est == pytest.approx(12_345.0) and rtt == pytest.approx(4000.0)
    p = cs.Path(base_ns=2000, asym_ns=600, queue_ns=0, stamp_ns=0)
    est, _ = cs.exchange(Zero(), 0.0, p, False)
    assert est == pytest.approx(300.0)                       # half the asymmetry, whatever the offset


def test_transparent_clocks_remove_queueing():
    rng = np.random.default_rng(1)
    p = cs.Path(queue_ns=5000, stamp_ns=0)
    with_tc = [cs.exchange(rng, 0.0, p, True)[0] for _ in range(200)]
    without = [cs.exchange(rng, 0.0, p, False)[0] for _ in range(200)]
    assert max(map(abs, with_tc)) < 1e-6 and np.std(without) > 3000


def test_servo_converges_and_fixture():
    r = cs.simulate(hours=0.1, transparent=True)
    tail = r["offset_ns"][len(r["offset_ns"]) // 2:]
    assert np.abs(tail).max() < 100 and abs(r["offset_ns"][0]) > 500
    here = pathlib.Path(__file__).resolve().parents[1] / "data" / "fixture_servo.csv"
    rows = [list(map(float, x.split(","))) for x in here.read_text().splitlines()[1:]]
    s = cs.Servo()
    for off, itv, step, freq in rows:
        got, f = s.update(off, itv)
        assert got == pytest.approx(step, rel=1e-6, abs=1e-6) and f == pytest.approx(freq, rel=1e-6, abs=1e-6)


def test_allan_and_holdover_and_compliance():
    rng = np.random.default_rng(4)
    white = rng.normal(0, 10.0, 20_000)                       # white phase noise, 10 ns
    a = dict(cs.allan_deviation(white, 1.0, (1, 10, 100)))
    assert 8 < a[1.0] / a[10.0] < 12 and 8 < a[10.0] / a[100.0] < 12       # slope -1
    assert cs.holdover_s(100_000, 0.0, 50.0) == pytest.approx(2000.0)
    t = cs.holdover_s(100_000, 0.0, 1.0, 1e-4)
    assert 0.5 * 1e-4 * t * t + t == pytest.approx(100_000, rel=1e-9)
    assert math.isinf(cs.holdover_s(100_000, 0.0, 0.0))
    c = cs.compliance([10, -150, 50], 100)
    assert c["max_abs_ns"] == 150 and c["share_within"] == pytest.approx(2 / 3)
