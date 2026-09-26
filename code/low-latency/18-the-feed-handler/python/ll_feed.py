"""Chapter 18 -- a minute at the open for the feed handler (the simulator with a burst and impaired lines), and the
weekend problem's arithmetic: the receive buffer a handler needs to absorb a burst, and the staleness a snapshot
interval implies."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
for c in ("feedhandler", "exchsim", "tape"):
    sys.path.insert(0, str(ROOT / "code/firm" / c))
import firm_feedhandler as fh  # noqa: E402
import make_feed_fixtures as mk  # noqa: E402

SEC = mk.SEC
OPEN = mk.OPEN
# A busy instrument whose activity is sixteen times its midday level at the open and decays over the minute, both lines
# impaired (independent and burst loss, jitter with reordering), an outage on both lines overlapping by 15 ms at 40 s,
# and snapshots once a second.
TAPE = dict(mk.TAPE, u_shape=15.0)
FEED = dict(loss=0.002, burst_loss=(0.0005, 0.1, 0.8), jitter_ns=20_000, reorder_window=4, snapshot_every_ns=SEC,
            outages=(("A", OPEN + 40 * SEC, OPEN + 40 * SEC + 30_000_000),
                     ("B", OPEN + 40 * SEC + 15_000_000, OPEN + 40 * SEC + 45_000_000)))


def minute(seconds=60.0):
    return mk.simulate(seconds, feed=FEED, tape=TAPE)


def rate_per_100ms(clean):
    """Messages published per 100 ms after the open."""
    counts = {}
    for t, p in fh.recorded(clean):
        n = len(fh.blocks(p)[1])
        if n:
            k = (t - OPEN) // (SEC // 10)
            counts[k] = counts.get(k, 0) + n
    return counts


def backlog(burst_rate, service_rate, seconds):
    """Datagrams queued at the end of a burst when the handler serves fewer than arrive (0 if it keeps up)."""
    return max(0.0, (burst_rate - service_rate) * seconds)


def rcvbuf_needed(backlog_packets, charged_bytes):
    """SO_RCVBUF to request: the kernel charges each datagram charged_bytes against the granted buffer, and grants
    twice what is asked (socket(7))."""
    return backlog_packets * charged_bytes / 2


def snapshot_staleness(interval_s, load_s=0.0):
    """Mean and worst time from an unrecoverable gap to a rebuilt book."""
    return interval_s / 2 + load_s, interval_s + load_s
