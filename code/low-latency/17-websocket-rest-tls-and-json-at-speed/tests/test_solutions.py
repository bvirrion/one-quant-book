"""Numbers gate, Book 13 chapter 17."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import ll_web as w  # noqa: E402

ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "code/firm/wsclient"))
import firm_wsclient as ws  # noqa: E402


def web():
    return {r["key"]: float(r["ns"]) for r in w.read("measured_web.csv")}


def tls():
    return {r["key"]: float(r["us"]) for r in w.read("measured_tls.csv")}


def test_exercises():
    assert w.masked_frame_bytes(300) == 308 and w.masked_frame_bytes(70_000) == 70_014
    assert len(ws.encode_frame(b"x" * 100)) == 102
    assert len(ws.encode_frame(b"x" * 300, mask_key=b"abcd")) == 308
    # exercise 4: SHA-256 compressions, with a 64-byte key (not hashed first) and a 119-byte payload
    blocks = lambda n: (n + 9 + 63) // 64                                                 # noqa: E731
    assert blocks(64 + 119) + blocks(64 + 32) == 5 and blocks(64 + 119) - 1 + blocks(64 + 32) - 1 == 3
    assert ws.fixed("64123.2") == 6_412_320_000_000                                       # exercise 5
    t = tls()
    assert round(w.new_connection_us(500, t["handshake_full"]) / 1000, 1) == 3.1          # exercise 2
    assert round(w.new_connection_us(500, t["handshake_resumed"]) / 1000, 1) == 2.6


def test_problem():
    c, p = w.budget("cpp"), w.budget("python")
    ct, pt = sum(c.values()), sum(p.values())
    assert round(ct, 1) == 0.9 and round(pt) == 48 and round(ct, 2) == 0.93 and round(pt, 1) == 47.6
    assert round(pt, -1) == 50 and round(ct) == 1                                        # introduction: almost 50, about one
    assert max(c, key=c.get) == "json" and max(p, key=p.get) == "frame_decode"
    assert round(c["json"], 2) == 0.39 and round(p["frame_decode"]) == 16 and round(p["frame_encode"]) == 15
    assert round(w.cpu_share(ct, 250) * 100, 1) == 0.2 and round(w.cpu_share(pt, 250) * 100, 1) == 8.7
    mixed = pt - p["frame_decode"] - p["frame_encode"] + c["frame_decode"] + c["frame_encode"]
    assert round(mixed, 1) == 16.9 and round(w.cpu_share(mixed, 250) * 100, 1) == 3.3
    assert round((p["frame_decode"] + p["frame_encode"]) / pt, 2) in (0.64, 0.65, 0.66, 0.67)   # two-thirds
    t = tls()
    assert round(w.new_connection_us(500, t["handshake_full"], websocket_upgrade=True) / 1000, 1) == 3.6
    assert round(1e6 / w.new_connection_us(500, t["handshake_full"]), -1) == 330
    wb = web()
    assert round(5000 * wb["depth_index"] * 1e-9 * 100, 1) == 0.2 and round(5000 * wb["py_depth"] * 1e-9 * 100, 1) == 4.9


def test_measured():
    t, wb = tls(), web()
    assert 500 < t["handshake_full"] < 6000 and t["handshake_resumed"] < t["handshake_full"]
    assert round(t["handshake_full"] / 1000, 1) == 2.1 and round(t["handshake_resumed"] / 1000, 1) == 1.6
    assert t["rtt_plain"] < t["rtt_tls"] < 3 * t["rtt_plain"] and round(t["rtt_tls"]) in (44, 45) and round(t["rtt_plain"]) == 33
    assert 0.05 < wb["aead_seal"] / 1000 < 0.2 and round(wb["aead_seal"] / 1000, 2) == 0.16
    assert round(wb["aead_open"] / 1000, 2) == 0.15
    assert t["handshake_full"] * 1000 / wb["aead_seal"] > 5000                     # ten thousand times dearer
    assert 10 < wb["frame_decode"] < 60 and round(wb["frame_decode"]) == 24 and round(wb["frame_encode"]) == 16
    assert 300 < wb["py_frame_decode"] / wb["frame_decode"] < 1000                     # several hundred times more
    assert round(wb["py_frame_decode"] / 1000) == 16 and round(wb["depth_index"] / 1000, 2) == 0.39
    assert round(wb["depth_naive"] / wb["depth_index"]) == 7
    assert round(wb["depth_naive"] / 1000, 1) == 2.6 and round(wb["py_depth"] / 1000) == 10
    assert round(wb["sign_precomputed"] / 1000, 2) == 0.64 and round(wb["sign_rekey"] / 1000, 1) == 1.1
    assert round(1 - wb["sign_precomputed"] / wb["sign_rekey"], 1) == 0.4             # about two-fifths
    assert round(wb["sign_openssl_pre"] / 1000, 2) == 0.19 and round(wb["sign_openssl"] / 1000, 2) == 0.92
    assert round(1 - wb["sign_openssl_pre"] / wb["sign_openssl"], 1) == 0.8            # four-fifths
