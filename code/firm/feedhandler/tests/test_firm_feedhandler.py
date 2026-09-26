import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_feedhandler as fh  # noqa: E402
import make_feed_fixtures as mk  # noqa: E402

DATA = HERE / "data"


def fixture():
    return [(DATA / f"{n}.bin").read_bytes() for n in ("lineA", "lineB", "clean", "snapshot")]


def test_expected_results_are_current():
    got = [f"{k} {mk.summary(h)}" for k, h in mk.runs(*fixture()).items()]
    assert got == (DATA / "expected.txt").read_text().splitlines()[1:]


def test_retransmission_recovers_the_clean_output_exactly():
    r = mk.runs(*fixture())
    assert r["retx"].hash == r["clean"].hash and r["retx"].events == r["clean"].events
    assert r["retx"].counters["retransmissions"] == 1 and r["retx"].counters["filled_by_line"] >= 1
    assert all(e > s for s, e in r["retx"].stale)


def test_snapshot_recovery_rebuilds_the_same_book():
    r = mk.runs(*fixture())
    snap, clean = r["snapshot"], r["clean"]
    assert snap.counters["snapshots"] == 1
    assert fh.book(snap.events) == fh.book(clean.events)                 # the same book at the end of the day
    g = next(i for i, e in enumerate(snap.events) if e[0] == ord("G"))
    upto = snap.events[g][6]
    after = [e for e in snap.events[g:] if e[0] not in (ord("G"), ord("W"), ord("H")) and e[3] > upto]
    assert after == [e for e in clean.events if e[3] > upto]            # every later event identical
    worst = max(e - s for s, e in snap.stale)
    assert 50_000_000 < worst <= 250_000_000 + 30_000_000               # waited for the next snapshot cycle


def test_arbitration_basics():
    def packet(seq, n):
        return b"SIMX      " + seq.to_bytes(8, "big") + n.to_bytes(2, "big") + b"".join(
            (19).to_bytes(2, "big") + b"D" + bytes(10) + (seq + k).to_bytes(8, "big") for k in range(n))
    ev = [(10, "A", packet(1, 2)), (11, "B", packet(1, 2)), (20, "B", packet(5, 1)), (21, "A", packet(3, 2)),
          (22, "A", packet(5, 1))]
    h = fh.Handler().run(ev)
    assert [e[5] for e in h.events] == [1, 2, 3, 4, 5]                   # refs in sequence order
    assert h.counters["duplicates"] == 2 and h.counters["gaps"] == 1 and h.counters["filled_by_line"] == 1
    assert h.stale == [(20, 21)]
