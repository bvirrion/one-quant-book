import pathlib
import random
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_nicring as nr  # noqa: E402


def test_fixture_is_reproduced():
    ev = [tuple(int(x) if x.isdigit() else x for x in line.split())
          for line in (HERE / "data" / "events.txt").read_text().splitlines()]
    rows = [r.split() for r in (HERE / "data" / "expected.txt").read_text().splitlines() if not r.startswith("#")]
    for f in rows:
        r = nr.Ring(int(f[0]), int(f[1])).run(ev)
        assert [r.rx, r.drops, r.processed, r.doorbells, r.max_owned] == [int(x) for x in f[2:7]]
        assert f"{r.hash:016x}" == f[7]


def test_full_ring_drops_and_refill_batches():
    r = nr.Ring(4, 4)
    assert [r.nic_rx(s, 64) for s in range(6)] == [True] * 4 + [False] * 2
    assert r.poll(3) == 3 and not r.nic_rx(6, 64)          # processed but not handed back: still full
    assert r.poll(1) == 1 and r.doorbells == 1 and r.nic_rx(6, 64)
    with pytest.raises(ValueError):
        nr.Ring(12, 1)


def test_no_loss_or_duplication_under_random_interleavings():
    for seed in range(20):
        rng = random.Random(seed)
        r = nr.Ring(32, rng.choice([1, 4, 8, 32]))
        accepted, done = [], []
        seq = 0
        for _ in range(2000):
            if rng.random() < 0.55:
                if r.nic_rx(seq, 100):
                    accepted.append(seq)
                seq += 1
            else:
                start = r.processed
                r.poll(rng.randint(1, 8))
                done.extend(accepted[start:r.processed])
        assert r.rx == len(accepted) and r.rx + r.drops == seq
        assert done == accepted[:r.processed]                  # every accepted packet, once, in order
        assert r.processed <= r.rx
