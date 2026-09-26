"""Numbers gate, Book 13 chapter 12."""
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import ll_queue as q  # noqa: E402


def near(x, want, rel=0.3):
    return abs(x - want) <= rel * want


def test_sizing():
    assert q.ring_for(0.9, 1.0, 1e-9) == 256 and math.ceil(math.log(1e-9) / math.log(0.9)) == 197
    assert round(q.time_to_overrun(65_536, 2e6, 1.5e6) * 1e3) == 131
    assert 70_001 - 69_500 == 501 and 70_001 % 1024 == 369 and 1024 - 501 == 523        # exercise 1
    assert round(2**64 / 2.5e8 / 3.156e7) == 2338 and round(2**32 / 2.5e8, 1) == 17.2     # exercise 2
    assert q.ring_for(0.8, 1.0, 1e-6) == 64 and math.ceil(math.log(1e-6) / math.log(0.8)) == 62   # exercise 3
    assert round(q.time_to_overrun(131_072, 3e6, 4e5) * 1e3, 1) == 50.4                  # exercise 5


def test_problem():
    assert 65_536 * 64 == 4 << 20
    assert (300_000 / 4e6, 300_000 / 2.5e6, 300_000 / 1.5e6) == (0.075, 0.12, 0.2)
    assert 0.5 * (2e6 - 1.5e6) == 250_000 and 262_144 * 64 == 16 << 20
    assert 5000 * 64 == 320_000 and q.conflated_share(2e6, 1.5e6) == 0.25


def test_measured():
    r = q.rtt()
    ring = r[("SPSC ring", "neighbours")]
    assert 120 < ring["p50"] < 320                                                        # about 200 ns
    assert near(r[("SPSC over shared memory", "neighbours")]["p50"], ring["p50"], 0.3)    # the same between processes
    locked = r[("mutex+condvar queue", "neighbours")]["p50"]
    assert 15_000 < locked < 60_000 and locked / ring["p50"] > 100                        # about 30 us, over a hundred times
    assert 1.5e8 < q.throughput() < 4e8                                                    # about 250 million a second
