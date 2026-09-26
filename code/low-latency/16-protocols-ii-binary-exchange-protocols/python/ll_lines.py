"""Chapter 16 -- recorded A and B lines from Book 10's exchange simulator, the arbitration of the two lines, and the
arithmetic of losing a message on both.

    record(seconds, out_dir, seed)      run the simulator (one instrument, Book 7's tape as background) with lossy
                                        lines from the open and write lineA.bin and lineB.bin (recorded-file format)
    packets(path) -> [(send_ns, packet)]
    line_gaps(pkts) / arbitrate(a, b)   gap counts: (packets, messages, gaps, missing messages)
    both_lost_independent(p) / both_lost_burst(...) / snapshot_recovery_s(...)   the weekend problem's models
"""
import dataclasses
import heapq
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("exchsim", "tape"):
    sys.path.insert(0, str(ROOT / "code/firm" / c))

SEC = 1_000_000_000
OPEN = 34_200 * SEC
# Loss on each line: independent 0.1% per packet, Gilbert-Elliott bursts (good->bad 0.05%, bad->good 10%, 80% lost
# in the bad state), and an outage of 60 ms on each line overlapping by 25 ms, 10 s after the open.
FEED = dict(loss=0.001, burst_loss=(0.0005, 0.1, 0.8),
            outages=(("A", OPEN + 10 * SEC, OPEN + 10 * SEC + 60_000_000),
                     ("B", OPEN + 10 * SEC + 35_000_000, OPEN + 10 * SEC + 95_000_000)),
            )
# A busier tape than Book 7's defaults (about 575 feed messages a second), no news window.
TAPE = dict(lo_rate=40.0, in_spread=40.0, noise_mu=6.0, cancel=0.5, news_at=None)


def record(seconds, out_dir, seed=1):
    from firm_exchsim import ExchangeConfig, FeedConfig, Simulator, TapeBackground
    from firm_tape import TapeConfig
    cfg = dataclasses.replace(ExchangeConfig(), feed=FeedConfig(**FEED))
    sim = Simulator(cfg, seed=seed)
    sim.add_background(TapeBackground(TapeConfig(seconds=float(seconds), seed=7, **TAPE)))
    res = sim.run(until_ns=OPEN + int(seconds * SEC) + SEC)
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "lineA.bin").write_bytes(res.recorded(line="A"))
    (out / "lineB.bin").write_bytes(res.recorded(line="B"))
    return res


def packets(path):
    b = pathlib.Path(path).read_bytes()
    out, i = [], 0
    while i + 12 <= len(b):
        t, n = struct.unpack_from(">QI", b, i)
        out.append((t, b[i + 12:i + 12 + n]))
        i += 12 + n
    return out


def header(p):
    return struct.unpack_from(">QH", p, 10)          # (seq, count)


def gap_events(pkts):
    """(arrival time in s after the open, missing messages) for each gap on one line."""
    nxt, out = 1, []
    for t, p in pkts:
        seq, count = header(p)
        count = 0 if count == 0xFFFF else count
        if seq > nxt:
            out.append(((t - OPEN) / SEC, seq - nxt))
        nxt = max(nxt, seq + count)
    return out


def line_gaps(pkts):
    nxt, gaps, missing, msgs = 1, 0, 0, 0
    for _, p in pkts:
        seq, count = header(p)
        count = 0 if count == 0xFFFF else count
        if seq > nxt:
            gaps += 1
            missing += seq - nxt
        msgs += count
        nxt = max(nxt, seq + count)
    return len(pkts), msgs, gaps, missing


def arbitrate(a, b):
    """Merge the two lines in arrival order and keep each sequence number once (the CME recommendation: process by
    sequence number, discard what was already processed; a gap means a loss on both lines)."""
    merged = heapq.merge(((t, 0, p) for t, p in a), ((t, 1, p) for t, p in b), key=lambda x: (x[0], x[1]))
    nxt, gaps, missing, msgs, dups, used = 1, 0, 0, 0, 0, 0
    for _, _, p in merged:
        seq, count = header(p)
        count = 0 if count == 0xFFFF else count
        if count and seq + count <= nxt:
            dups += 1
            continue
        if seq > nxt:
            gaps += 1
            missing += seq - nxt
        msgs += seq + count - max(seq, nxt)
        nxt = max(nxt, seq + count)
        used += 1
    return used, msgs, gaps, missing, dups


# -- the weekend problem -------------------------------------------------------------------------------------------

def both_lost_independent(p):
    return p * p


def ge_stationary_loss(g2b, b2g, loss_bad, loss_good=0.0):
    pi_bad = g2b / (g2b + b2g)
    return pi_bad * loss_bad + (1 - pi_bad) * loss_good


def both_lost_common(p_line, p_common):
    """Each line loses a packet on its own with probability p_line; a common cause (a shared switch, the venue's own
    publisher) loses it on both with probability p_common."""
    return p_common + (1 - p_common) * p_line * p_line


def snapshot_recovery_s(interval_s, snapshot_s, replay_msgs=0, per_msg_s=0.0, worst=False):
    """Time from detecting an unrecoverable gap to a rebuilt book: wait for the next snapshot cycle (uniform, so half
    the interval on average, the whole interval at worst), read it, then apply the incremental messages buffered
    meanwhile."""
    wait = interval_s if worst else interval_s / 2
    return wait + snapshot_s + replay_msgs * per_msg_s


if __name__ == "__main__":
    import time
    t = time.time()
    record(float(sys.argv[1]) if len(sys.argv) > 1 else 20.0, sys.argv[2] if len(sys.argv) > 2 else "/tmp/lines")
    print(f"{time.time() - t:.1f} s")
