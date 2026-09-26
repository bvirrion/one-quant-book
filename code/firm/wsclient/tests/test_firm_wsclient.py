import hashlib
import hmac
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_wsclient as ws  # noqa: E402
import make_ws_fixtures as mk  # noqa: E402
from firm_ratelimit import Governor, Rule  # noqa: E402

DATA = HERE / "data"


def test_rfc6455_frame_forms():
    # the RFC's own examples (section 5.7): an unmasked and a masked "Hello", a 256-byte and a 65536-byte binary
    assert ws.encode_frame(b"Hello") == bytes.fromhex("810548656c6c6f")
    assert ws.encode_frame(b"Hello", mask_key=bytes.fromhex("37fa213d")) == bytes.fromhex("818537fa213d7f9f4d5158")
    assert ws.encode_frame(b"x" * 256, ws.OP_BINARY)[:4] == bytes.fromhex("827e0100")
    assert ws.encode_frame(b"x" * 65536, ws.OP_BINARY)[:10] == bytes.fromhex("827f0000000000010000")
    f, used = ws.decode_frame(bytes.fromhex("818537fa213d7f9f4d5158"))
    assert (f.payload, f.masked, used) == (b"Hello", True, 11)
    assert ws.decode_frame(bytes.fromhex("8185"))[0] is None                 # incomplete
    with pytest.raises(ws.FrameError):
        ws.encode_frame(b"x" * 126, ws.OP_PING)
    with pytest.raises(ws.FrameError):
        ws.decode_frame(bytes.fromhex("817e0005") + b"hello")                 # 5 must use the 7-bit form


def test_fragments_and_control_frames():
    r = ws.Reassembler()
    assert r.feed(ws.Frame(False, ws.OP_TEXT, b"Hel")) == []
    assert r.feed(ws.Frame(True, ws.OP_PING, b"")) == [ws.Message(ws.OP_PING, b"")]
    assert r.feed(ws.Frame(True, ws.OP_CONT, b"lo")) == [ws.Message(ws.OP_TEXT, b"Hello")]
    with pytest.raises(ws.FrameError):
        r.feed(ws.Frame(True, ws.OP_CONT, b"?"))


def test_fixture_stream_reassembles():
    buf, out, r = (DATA / "frames.bin").read_bytes(), [], ws.Reassembler()
    while buf:
        f, used = ws.decode_frame(buf)
        out += r.feed(f)
        buf = buf[used:]
    want = [line.split(" ") for line in (DATA / "frames_expected.txt").read_text().splitlines()]
    assert [(m.opcode, m.payload.hex()) for m in out] == [(int(o), p) for o, p in want]


def test_depth_decoding_is_exact():
    d = ws.decode_depth('{"e":"depthUpdate","E":1,"s":"BNBBTC","U":157,"u":160,"b":[["0.0024","10"]],'
                        '"a":[["0.0026","100"]]}')
    assert (d.first, d.last, d.bids, d.asks) == (157, 160, [(240_000, 10 * ws.SCALE)], [(260_000, 100 * ws.SCALE)])
    assert ws.to_book_levels([(6_412_345_000_000, 25_000_000)], tick=1_000_000, lot=100_000) == [(6_412_345, 250)]
    lines = (DATA / "depth_updates.jsonl").read_text().splitlines()
    assert (DATA / "depth_expected.txt").read_text().splitlines() == [mk.line(ws.decode_depth(x)) for x in lines]


def test_signer_matches_rfc4231_and_the_venue_example():
    assert ws.Signer(b"\x0b" * 20).sign(b"Hi There") == \
        "b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7"
    assert ws.Signer("Jefe").sign("what do ya want for nothing?") == \
        "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"
    payload = "symbol=LTCBTC&side=BUY&type=LIMIT&timeInForce=GTC&quantity=1&price=0.1&recvWindow=5000&timestamp=1499827319559"
    secret = "NhqPtmdSJYdKjVHjA7PZj4Mge3R5YNiP1e3UZjInClVN65XAbvqqM6A7H5fATj0j"
    s = ws.Signer(secret)
    assert s.sign(payload) == "c8db56825ae71d6d79447849e617115f4a920fa2acdcab2b053c4b2838bd6b71"
    assert s.sign(payload) == hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()   # reusable


def test_pool_reuses_connections_and_respects_the_governor():
    g = Governor([Rule("weight", 1000, 3)])
    p = ws.Pool(2, g)
    assert [p.request(0) for _ in range(3)] == ["opened", "opened", "full"]
    p.done()
    assert p.request(1) == "reused" and p.handshakes == 2
    p.done()
    assert p.request(2) == "throttled" and p.refused == 1          # 3 units of weight per second used up
    assert p.request(1000) == "reused" and p.handshakes == 2       # a new window
