"""Write firm.ticktotrade's fixture: the book builder's small-tick day (6,000 events, chapter 19) encoded as the
simulator's market-data feed (Book 10's PROTOCOL.md: ITCH-style messages in MoldUDP64 packets), in the recorded-file
format of firm.feedhandler (u64 send time | u32 length | packet, big-endian). The harness sends every packet on line A
and, 5 us later, on line B; the feed handler turns them back into the same 6,000 events.

data/line.bin       the recorded line: packets of up to 5 messages, sent at the time of their first message
"""
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
for c in ("exchsim", "feedhandler", "bookbuilder"):
    sys.path.insert(0, str(HERE.parent / c))
import firm_exchsim_codec as c  # noqa: E402
import make_book_fixtures as mk  # noqa: E402

PER_PACKET = 5


def message(e):
    kind, side, locate, seq, ts, ref, ref2, price, qty = e
    k = chr(kind)
    f = c.NT["feed"][k]
    if k == "A":
        return f(locate, 0, ts, ref, chr(side), qty, "SIM1", price)
    if k == "E":
        return f(locate, 0, ts, ref, qty, ref2)
    if k == "X":
        return f(locate, 0, ts, ref, qty)
    if k == "D":
        return f(locate, 0, ts, ref)
    if k == "U":
        return f(locate, 0, ts, ref, ref2, qty, price)
    raise ValueError(k)


def line(events):
    out = b""
    for i in range(0, len(events), PER_PACKET):
        chunk = events[i:i + PER_PACKET]
        pkt = c.mold_packet("SIMX", chunk[0][3], [c.encode("feed", message(e)) for e in chunk])
        out += struct.pack(">QI", chunk[0][4], len(pkt)) + pkt
    return out


def main():
    ev = mk.unpack((HERE.parent / "bookbuilder/data/events_small.bin").read_bytes())
    (HERE / "data/line.bin").write_bytes(line(ev))


if __name__ == "__main__":
    main()
