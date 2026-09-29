import pathlib
import struct
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_wirecap as wc  # noqa: E402


def test_frames_parse_back():
    payload = struct.pack(">10sQH", b"SESSION001", 42, 2) + struct.pack(">H", 3) + b"abc" + struct.pack(">H", 1) + b"z"
    fr = wc.udp_frame("10.0.0.1", "239.1.1.1", 1, 2, payload)
    p = wc.parse(fr)
    assert (p["proto"], p["src"], p["dst"], p["dport"], p["payload"]) == ("udp", "10.0.0.1", "239.1.1.1", 2, payload)
    assert wc.mold(p["payload"]) == (b"SESSION001", 42, 2, [b"abc", b"z"])
    assert wc._csum(fr[14:34]) == 0                                 # a valid IPv4 header checksum
    t = wc.parse(wc.tcp_frame("10.0.1.5", "10.0.2.9", 3, 4, 7, wc.ORDER.pack(b"O", 9, 42)))
    assert t["proto"] == "tcp" and wc.ORDER.unpack(t["payload"]) == (b"O", 9, 42)


def test_trailer_round_trip():
    fr = wc.udp_frame("10.0.0.1", "239.1.1.1", 1, 2, b"x" * 30)
    tr = wc.add_trailer(fr, 34_200_123_456_789, device=7, port=12)
    back, t, dev, port = wc.strip_trailer(tr)
    assert back == fr and (t, dev, port) == (34_200_123_456_789, 7, 12)
    assert wc.strip_trailer(fr)[1] is None
    assert wc.parse(tr)["payload"] == b"x" * 30                        # the IP length ignores the trailer


def test_pcap_and_pcapng_round_trip(tmp_path):
    rec = [(34_200_000_000_001, b"\x01" * 60), (34_200_000_000_999, b"\x02" * 80)]
    wc.write_pcap(tmp_path / "a.pcap", rec)
    wc.write_pcapng(tmp_path / "a.pcapng", rec)
    assert wc.read_pcap(tmp_path / "a.pcap") == rec and wc.read_pcapng(tmp_path / "a.pcapng") == rec
    (tmp_path / "bad.pcap").write_bytes(struct.pack("<IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1))
    with pytest.raises(ValueError):
        wc.read_pcap(tmp_path / "bad.pcap")


def test_matching_gaps_bursts_and_fixture():
    feed = {10: 1000, 11: 1500, 12: 1600}
    assert wc.match_orders(feed, [(2000, 11), (2100, 99)]) == [(2000, 1500)]
    assert wc.match_nearest([1000, 1500, 1600], [1550, 900]) == [1500, None]
    assert wc.gaps([1, 2, 5, 6, 9]) == [(3, 2), (7, 2)]
    b = wc.bursts([0, 10, 20, 5000], [1250, 1250, 1250, 100], 1000, 10.0)
    assert b == [(0, 30.0)]
    back = wc.read_pcap(HERE / "data" / "fixture.pcap")
    n, nb, first, last, _ = (HERE / "data" / "fixture_expected.txt").read_text().split()
    assert (len(back), sum(len(f) for _, f in back), back[0][0], back[-1][0]) == (int(n), int(nb), int(first), int(last))
