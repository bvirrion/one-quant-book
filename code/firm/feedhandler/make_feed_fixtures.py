"""Write firm.feedhandler's fixtures from Book 10's simulator (deterministic, seeded; not a real venue's data).

Three seconds of a busy instrument from the open, with both lines impaired: independent loss (0.3% per packet),
jitter with reordering, and outages of 30 ms on each line overlapping by 12 ms; snapshots every 250 ms.
    data/lineA.bin, data/lineB.bin   the two lines as received (recorded-file format)
    data/clean.bin                   the lossless packet stream (what the retransmission server holds)
    data/snapshot.bin                the snapshot channel
    data/expected.txt                the Python reference's results for three runs: clean, impaired with the
                                     retransmission server, impaired without it (snapshot recovery)
"""
import dataclasses
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
for c in ("exchsim", "tape"):
    sys.path.insert(0, str(HERE.parent / c))
import firm_feedhandler as fh  # noqa: E402

SEC = 1_000_000_000
OPEN = 34_200 * SEC
FEED = dict(loss=0.003, jitter_ns=20_000, reorder_window=4, snapshot_every_ns=SEC // 4,
            outages=(("A", OPEN + 1_500_000_000, OPEN + 1_530_000_000),
                     ("B", OPEN + 1_518_000_000, OPEN + 1_548_000_000)))
TAPE = dict(lo_rate=40.0, in_spread=40.0, noise_mu=6.0, cancel=0.5, news_at=None)


def simulate(seconds=3.0, seed=1, feed=None, tape=None):
    from firm_exchsim import ExchangeConfig, FeedConfig, Simulator, TapeBackground
    from firm_exchsim_codec import file_record
    from firm_tape import TapeConfig
    cfg = dataclasses.replace(ExchangeConfig(), feed=FeedConfig(**(feed or FEED)))
    sim = Simulator(cfg, seed=seed)
    sim.add_background(TapeBackground(TapeConfig(seconds=seconds, seed=7, **(tape or TAPE))))
    res = sim.run(until_ns=OPEN + int(seconds * SEC) + SEC // 2)
    clean = b"".join(file_record(t, p) for t, p in res.packets())
    return res.recorded(line="A"), res.recorded(line="B"), clean, res.snapshot_bytes()


def runs(a, b, clean, snap):
    ev = fh.merge(a, b, snap)
    return {"clean": fh.Handler().run(fh.merge(clean, b"", b"")),
            "retx": fh.Handler(retx=fh.RetxServer(fh.recorded(clean), window=100_000)).run(ev),
            "snapshot": fh.Handler(retx=None).run(ev)}


def summary(h):
    c = h.counters
    stale_ns = sum(e - s for s, e in h.stale)
    return (f"{len(h.events)} {h.hash:016x} {len(h.stale)} {stale_ns} {c['packets']} {c['duplicates']} {c['gaps']} "
            f"{c['filled_by_line']} {c['retransmissions']} {c['snapshots']}")


def main():
    data = HERE / "data"
    data.mkdir(exist_ok=True)
    a, b, clean, snap = simulate()
    for name, x in (("lineA", a), ("lineB", b), ("clean", clean), ("snapshot", snap)):
        (data / f"{name}.bin").write_bytes(x)
    lines = ["# run events hash stale_intervals stale_ns packets duplicates gaps filled_by_line retransmissions "
             "snapshots"]
    lines += [f"{k} {summary(h)}" for k, h in runs(a, b, clean, snap).items()]
    (data / "expected.txt").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
