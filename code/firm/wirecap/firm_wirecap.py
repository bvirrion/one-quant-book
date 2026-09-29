"""firm.wirecap -- packet captures of the firm's own traffic (build of One Quant Book 14, chapter 5).

Writes and reads libpcap files with nanosecond timestamps (magic 0xA1B23C4D, link type 1, Ethernet) and a minimal
pcapng (section header, one interface with if_tsresol = 9, enhanced packet blocks); builds Ethernet/IPv4/UDP and
Ethernet/IPv4/TCP frames; appends and strips an optional 16-byte timestamp trailer (device, port, flags, seconds,
nanoseconds: a layout of this book's own, in the style of the capture devices' trailers); parses the simulator's
MoldUDP64 packets and the firm's order messages; matches orders to trigger packets; finds sequence gaps per stream
and bursts per window. A C++20 reader (cpp/firm_wirecap.hpp) reproduces the Python reader's counts and checksums on
data/fixture.pcap.

API (stable):
    udp_frame(src_ip, dst_ip, sport, dport, payload, src_mac, dst_mac) -> bytes      (IPv4 checksum computed)
    tcp_frame(src_ip, dst_ip, sport, dport, seq, payload, src_mac, dst_mac) -> bytes
    add_trailer(frame, t_ns, device, port) -> bytes ; strip_trailer(frame) -> (frame, t_ns, device, port)
    write_pcap(path, records) ; read_pcap(path) -> [(t_ns, frame)]           records: (t_ns, frame bytes)
    write_pcapng(path, records) ; read_pcapng(path) -> [(t_ns, frame)]
    parse(frame) -> dict(proto, src, dst, sport, dport, payload)              IPv4 UDP or TCP, else None
    mold(payload) -> (session, seq, count, [messages])
    ORDER = struct '>cQI' (type 'O', client order id, trigger sequence)       the firm's order message (book's own)
    match_orders(feed, orders) -> list[(order_t, trigger_t)]       by the trigger sequence carried in the order
    match_nearest(feed_trigger_t, order_t) -> list[trigger_t]                 the naive rule: the latest trigger before
    gaps(seqs) -> list[(first_missing, count)]
    bursts(t_ns, nbytes, window_ns, threshold_gbps) -> list[(start_ns, gbps)]
"""
import ipaddress
import struct

MAGIC_NS = 0xA1B23C4D
LINKTYPE_ETHERNET = 1
TRAILER = struct.Struct(">HHIII")          # device, port, flags (reserved), seconds, nanoseconds: 16 bytes
TRAILER_TAG = 0x7E00                       # top byte of the device field marks the trailer (this book's layout)
ORDER = struct.Struct(">cQI")


def _mac(s):
    return bytes(int(x, 16) for x in s.split(":"))


def _csum(b):
    if len(b) % 2:
        b += b"\0"
    s = sum(struct.unpack(f">{len(b) // 2}H", b))
    while s >> 16:
        s = (s & 0xFFFF) + (s >> 16)
    return ~s & 0xFFFF


def _ip(src, dst, proto, body):
    hdr = struct.pack(">BBHHHBBH4s4s", 0x45, 0, 20 + len(body), 0, 0x4000, 64, proto, 0,
                      ipaddress.IPv4Address(src).packed, ipaddress.IPv4Address(dst).packed)
    return hdr[:10] + struct.pack(">H", _csum(hdr)) + hdr[12:] + body


def udp_frame(src_ip, dst_ip, sport, dport, payload, src_mac="02:00:00:00:00:01", dst_mac="01:00:5e:00:00:01"):
    udp = struct.pack(">HHHH", sport, dport, 8 + len(payload), 0) + payload
    return _mac(dst_mac) + _mac(src_mac) + b"\x08\x00" + _ip(src_ip, dst_ip, 17, udp)


def tcp_frame(src_ip, dst_ip, sport, dport, seq, payload, src_mac="02:00:00:00:00:02", dst_mac="02:00:00:00:00:03"):
    tcp = struct.pack(">HHIIBBHHH", sport, dport, seq, 0, 5 << 4, 0x18, 65535, 0, 0) + payload
    return _mac(dst_mac) + _mac(src_mac) + b"\x08\x00" + _ip(src_ip, dst_ip, 6, tcp)


def add_trailer(frame, t_ns, device=1, port=1):
    return frame + TRAILER.pack(TRAILER_TAG | (device & 0xFF), port, 0, t_ns // 1_000_000_000, t_ns % 1_000_000_000)


def strip_trailer(frame):
    dev, port, _, sec, ns = TRAILER.unpack(frame[-16:])
    if dev & 0xFF00 != TRAILER_TAG:
        return frame, None, None, None
    return frame[:-16], sec * 1_000_000_000 + ns, dev & 0xFF, port


def write_pcap(path, records):
    with open(path, "wb") as f:
        f.write(struct.pack("<IHHiIII", MAGIC_NS, 2, 4, 0, 0, 65535, LINKTYPE_ETHERNET))
        for t, fr in records:
            f.write(struct.pack("<IIII", t // 1_000_000_000, t % 1_000_000_000, len(fr), len(fr)) + fr)


def read_pcap(path):
    b = open(path, "rb").read()
    magic, _, _, _, _, _, link = struct.unpack_from("<IHHiIII", b, 0)
    if magic != MAGIC_NS or link != LINKTYPE_ETHERNET:
        raise ValueError("not a nanosecond Ethernet pcap written by this library")
    out, off = [], 24
    while off + 16 <= len(b):
        sec, ns, incl, _ = struct.unpack_from("<IIII", b, off)
        out.append((sec * 1_000_000_000 + ns, b[off + 16:off + 16 + incl]))
        off += 16 + incl
    return out


def _block(btype, body):
    pad = (-len(body)) % 4
    n = 12 + len(body) + pad
    return struct.pack("<II", btype, n) + body + b"\0" * pad + struct.pack("<I", n)


def write_pcapng(path, records):
    shb = _block(0x0A0D0D0A, struct.pack("<IHHq", 0x1A2B3C4D, 1, 0, -1))
    opts = struct.pack("<HHB3x", 9, 1, 9) + struct.pack("<HH", 0, 0)          # if_tsresol = 9 (ns), end of options
    idb = _block(0x00000001, struct.pack("<HHI", LINKTYPE_ETHERNET, 0, 65535) + opts)
    with open(path, "wb") as f:
        f.write(shb + idb)
        for t, fr in records:
            pad = fr + b"\0" * ((-len(fr)) % 4)
            f.write(_block(0x00000006, struct.pack("<IIIII", 0, t >> 32, t & 0xFFFFFFFF, len(fr), len(fr)) + pad))


def read_pcapng(path):
    b = open(path, "rb").read()
    out, off = [], 0
    while off + 12 <= len(b):
        btype, n = struct.unpack_from("<II", b, off)
        if btype == 0x00000006:
            _, hi, lo, cap, _ = struct.unpack_from("<IIIII", b, off + 8)
            out.append(((hi << 32) | lo, b[off + 28:off + 28 + cap]))
        off += n
    return out


def parse(frame):
    if len(frame) < 34 or frame[12:14] != b"\x08\x00":
        return None
    ihl = (frame[14] & 0x0F) * 4
    proto = frame[23]
    src, dst = str(ipaddress.IPv4Address(frame[26:30])), str(ipaddress.IPv4Address(frame[30:34]))
    total = struct.unpack_from(">H", frame, 16)[0]
    l4 = 14 + ihl
    end = 14 + total
    if proto == 17:
        sport, dport, _, _ = struct.unpack_from(">HHHH", frame, l4)
        return {"proto": "udp", "src": src, "dst": dst, "sport": sport, "dport": dport, "payload": frame[l4 + 8:end]}
    if proto == 6:
        sport, dport = struct.unpack_from(">HH", frame, l4)
        off = (frame[l4 + 12] >> 4) * 4
        return {"proto": "tcp", "src": src, "dst": dst, "sport": sport, "dport": dport, "payload": frame[l4 + off:end]}
    return None


def mold(payload):
    session, seq, count = struct.unpack_from(">10sQH", payload, 0)
    msgs, off = [], 20
    for _ in range(count if count != 0xFFFF else 0):
        n = struct.unpack_from(">H", payload, off)[0]
        msgs.append(payload[off + 2:off + 2 + n])
        off += 2 + n
    return session, seq, count, msgs


def match_orders(feed, orders):
    """feed: {sequence: capture time of the packet carrying it}; orders: [(capture time, trigger sequence)]."""
    return [(t, feed[s]) for t, s in orders if s in feed]


def match_nearest(trigger_t, order_t):
    import bisect
    out = []
    for t in order_t:
        i = bisect.bisect_right(trigger_t, t) - 1
        out.append(trigger_t[i] if i >= 0 else None)
    return out


def gaps(seqs):
    out, exp = [], None
    for s in sorted(set(seqs)):
        if exp is not None and s > exp:
            out.append((exp, s - exp))
        exp = s + 1
    return out


def bursts(t_ns, nbytes, window_ns, threshold_gbps):
    """Non-overlapping windows whose traffic exceeds threshold_gbps."""
    acc = {}
    for t, n in zip(t_ns, nbytes, strict=True):
        acc[t // window_ns] = acc.get(t // window_ns, 0) + n
    rate = {k: 8.0 * v / window_ns for k, v in acc.items()}
    return [(k * window_ns, r) for k, r in sorted(rate.items()) if r > threshold_gbps]
