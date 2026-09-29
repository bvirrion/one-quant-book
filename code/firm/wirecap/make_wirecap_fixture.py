"""Write data/fixture.pcap (a few hundred frames: feed datagrams with trailers, order segments) and the Python
reader's summary data/fixture_expected.txt, for the C++20 reader's test."""
import pathlib
import struct

import firm_wirecap as wc

HERE = pathlib.Path(__file__).resolve().parent


def records(n=300):
    out, t = [], 34_200 * 1_000_000_000
    for i in range(n):
        t += 1_000 + (i * 7919) % 50_000
        if i % 5:
            msg = struct.pack(">H", 36) + bytes(36)
            payload = struct.pack(">10sQH", b"SESSION001", 1000 + i, 1) + msg
            fr = wc.add_trailer(wc.udp_frame("10.0.0.1", "239.1.1.1", 30000, 30001, payload), t, 1, 3)
        else:
            fr = wc.tcp_frame("10.0.1.5", "10.0.2.9", 40000, 50000, i, wc.ORDER.pack(b"O", i, 1000 + i - 1))
        out.append((t, fr))
    return out


def main():
    rec = records()
    wc.write_pcap(HERE / "data" / "fixture.pcap", rec)
    back = wc.read_pcap(HERE / "data" / "fixture.pcap")
    h = 0xCBF29CE484222325
    for _, fr in back:
        for b in fr:
            h = ((h ^ b) * 0x100000001B3) & (1 << 64) - 1
    s = f"{len(back)} {sum(len(f) for _, f in back)} {back[0][0]} {back[-1][0]} {h:016x}\n"
    (HERE / "data" / "fixture_expected.txt").write_text(s)


if __name__ == "__main__":
    main()
