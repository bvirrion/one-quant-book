"""Write firm.bookbuilder's fixtures.

data/events_sim.bin     the normalised events of firm.feedhandler's clean fixture run (Book 10's simulator, a large-tick
                        instrument: the spread is one tick most of the time), 48-byte records as the handler hashes them
data/events_small.bin   a synthetic small-tick instrument: orders scattered up to 300 ticks from a random-walk mid,
                        cancels, reductions, replaces, and executions of resting orders the mid moves through,
                        6,000 events (not a real instrument's data)
data/expected.txt       per file: events, and the level-2 hash chained over every event (top five levels a side)
"""
import heapq
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "feedhandler"))
import firm_bookbuilder as bb  # noqa: E402
import firm_feedhandler as fh  # noqa: E402

B, S = bb.B, bb.S


def pack(events):
    return b"".join(fh.EVENT.pack(*e) for e in events)


def unpack(b):
    return [fh.EVENT.unpack_from(b, i) for i in range(0, len(b), fh.EVENT.size)]


def small_tick(n=6000, seed=11, tick=1, spread=300, drift=0.0):
    """Synthetic events: prices in units of 1e-4 with a 1-unit tick, around a mid that random-walks by up to 3 ticks
    per event (plus `drift` ticks per event)."""
    rng = random.Random(seed)
    mid, ref, live, out, seq = 1_000_000.0, 0, {}, [], 0

    def ev(kind, side=0, ref_=0, ref2=0, price=0, qty=0):
        nonlocal seq
        seq += 1
        out.append((ord(kind), side, 1, seq, 34_200_000_000_000 + seq * 1000, ref_, ref2, price, qty))

    heaps = {B: [], S: []}                 # (key, ref): max-heap of bids, min-heap of asks, dead entries skipped

    def best(side):
        h = heaps[side]
        while h and (h[0][1] not in live or live[h[0][1]][1] != abs(h[0][0])):
            heapq.heappop(h)
        return abs(h[0][0]) if h else None

    def price_for(side):
        """A price `off` ticks from the mid, never crossing the other side's best (no matching engine here)."""
        off = rng.randint(1, spread) * tick
        if side == B:
            best_ask = best(S)
            p = int(mid - off)
            return p if best_ask is None else min(p, best_ask - tick)
        best_bid = best(B)
        p = int(mid + off)
        return p if best_bid is None else max(p, best_bid + tick)

    def track(r):
        side, price, _ = live[r]
        heapq.heappush(heaps[side], (-price if side == B else price, r))

    while len(out) < n:
        mid += rng.randint(-3, 3) * tick + drift
        # the price moves through the book: resting orders on the wrong side of the mid are executed
        for side, sign in ((S, -1), (B, 1)):              # asks below the mid, bids above it
            p = best(side)
            while p is not None and sign * (p - mid) > 0 and len(out) < n:
                k = heaps[side][0][1]
                ev("E", 0, k, 0, 0, live[k][2])
                del live[k]
                p = best(side)
        if len(out) >= n:
            break
        r = rng.random()
        if r < 0.5 or not live:
            side = rng.choice((B, S))
            price = price_for(side)
            ref += 1
            live[ref] = [side, price, rng.randint(1, 20) * 100]
            track(ref)
            ev("A", side, ref, 0, price, live[ref][2])
        elif r < 0.8:
            k = rng.choice(list(live))
            ev("D", 0, k)
            del live[k]
        elif r < 0.9:
            k = rng.choice(list(live))
            q = min(live[k][2], rng.randint(1, 5) * 100)
            ev("X", 0, k, 0, 0, q)
            live[k][2] -= q
            if live[k][2] == 0:
                del live[k]
        else:
            k = rng.choice(list(live))
            side = live[k][0]
            price = price_for(side)
            ref += 1
            ev("U", 0, k, ref, price, live[k][2])
            live[ref] = [side, price, live.pop(k)[2]]
            track(ref)
    return out


def chained(events):
    book, h = bb.Book(), bb.FNV_OFFSET
    for e in events:
        book.apply(e)
        h = bb.l2_hash(book, 5, h)
    return h, book


def main():
    data = HERE / "data"
    data.mkdir(exist_ok=True)
    feed = HERE.parent / "feedhandler/data/clean.bin"
    sim = fh.Handler().run(fh.merge(feed.read_bytes(), b"", b"")).events
    small = small_tick()
    lines = []
    for name, ev in (("events_sim", sim), ("events_small", small)):
        (data / f"{name}.bin").write_bytes(pack(ev))
        h, _ = chained(ev)
        lines.append(f"{name} {len(ev)} {h:016x}")
    (data / "expected.txt").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
