import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_fixengine as fx  # noqa: E402

DATA = HERE / "data"


def raw(text):
    return text.strip().encode().replace(b"|", fx.SOH)


def test_published_example_body_length_and_checksum():
    m = fx.decode(raw((DATA / "wikipedia_example.fix").read_text()))
    assert m.get(9) == b"65" and m.get(10) == b"062" and m.msg_type == b"A" and m.seq == 177
    body = m.raw[m.raw.index(b"35="):m.raw.index(b"10=")]
    assert len(body) == 65 and fx.checksum(m.raw[:m.raw.index(b"10=")]) == 62


def test_corruptions_are_caught():
    good = raw((DATA / "wikipedia_example.fix").read_text())
    with pytest.raises(fx.FixError) as e:
        fx.decode(good.replace(b"SERVER", b"SERVEX"))
    assert e.value.kind == "checksum"
    with pytest.raises(fx.FixError) as e:
        fx.decode(good.replace(b"9=65", b"9=64"))
    assert e.value.kind == "body_length"
    with pytest.raises(fx.FixError) as e:
        fx.decode(good.replace(b"35=A\x01", b"").replace(b"9=65", b"9=60"))
    assert e.value.kind == "order"


def test_encode_round_trip_and_framing():
    a = fx.encode(b"D", [(11, "ORD1"), (55, "ESZ6"), (54, 1), (38, 5)], 2, "FIRM", "BROKER", 52_201_000)
    b = fx.encode(b"0", [], 3, "FIRM", "BROKER", 52_231_000)
    m = fx.decode(a)
    assert m.get(11) == b"ORD1" and m.get(52) == b"20260925-14:30:01.000" and m.seq == 2
    stream = a + b
    assert fx.frame(stream) == len(a) and fx.frame(stream[len(a):]) == len(b)
    assert fx.frame(stream[:len(a) - 1]) == 0 and fx.frame(b"8=FIX") == 0
    with pytest.raises(fx.FixError):
        fx.frame(b"XX=1\x01")


def test_golden_conversation_is_reproduced():
    s = fx.replay((DATA / "conversation.txt").read_text().splitlines())
    assert s.trace == (DATA / "expected_trace.txt").read_text().splitlines()
    assert s.state == "disconnected" and s.next_in == 10 and s.next_out == 8


def test_gap_resend_and_gap_fill():
    tr = fx.replay((DATA / "conversation.txt").read_text().splitlines()).trace
    rr = next(x for x in tr if " out " in x and "|35=2|" in x)
    assert "|7=4|16=0|" in rr and "|34=3|" in rr
    assert [x.split()[2] for x in tr if " deliver " in x] == ["2", "4", "6"]
    assert any("duplicate 6 ignored" in x for x in tr)
    ours = [x for x in tr if x.startswith("52270100 out")]
    assert "|35=4|" in ours[0] and "|34=3|" in ours[0] and "|123=Y|36=4|" in ours[0] and "|43=Y|" in ours[0]
    assert "|35=F|" in ours[1] and "|34=4|" in ours[1] and "|122=20260925-14:31:10.000|" in ours[1]


def test_heartbeat_test_request_and_timeout():
    s = fx.Session("FIRM", "BROKER", heartbeat_s=30)
    s.logon(0)
    s.on_bytes(fx.encode(b"A", [(98, 0), (108, 30)], 1, "BROKER", "FIRM", 5), 5)
    assert s.state == "active"
    assert b"35=0" in s.on_timer(30_000)[0]                  # we have been quiet for 30 s: heartbeat
    t = s.on_timer(36_005)                                   # the broker quiet for 36 s: test request
    assert b"35=1" in t[0] and b"112=TEST1" in t[0]
    assert s.on_timer(66_005) == [] and s.state == "disconnected"


def test_sequence_too_low_logs_out():
    s = fx.Session("FIRM", "BROKER")
    s.logon(0)
    s.on_bytes(fx.encode(b"A", [(108, 30)], 1, "BROKER", "FIRM", 1), 1)
    out, _ = s.on_bytes(fx.encode(b"0", [], 1, "BROKER", "FIRM", 2), 2)
    assert b"35=5" in out[0] and b"MsgSeqNum too low" in out[0] and s.state == "disconnected"


def test_reset_mode_moves_the_expected_number():
    s = fx.Session("FIRM", "BROKER")
    s.logon(0)
    s.on_bytes(fx.encode(b"A", [(108, 30)], 1, "BROKER", "FIRM", 1), 1)
    s.on_bytes(fx.encode(b"4", [(36, 500)], 7, "BROKER", "FIRM", 2), 2)
    assert s.next_in == 500


def test_a_checksum_field_inside_the_body_is_rejected():
    """Chapter 25's fuzzer: tag 11 turned into 10 and 34=2 into 34=3 keep the checksum, and the message was accepted."""
    m = (b"8=FIX.4.4\x019=117\x0135=8\x0149=BROKER\x0156=FIRM\x0134=3\x0152=20260925-14:30:01.002\x0137=X1\x01"
         b"10=ORD1\x0117=E1\x01150=0\x0139=0\x0155=ESZ6\x0154=1\x0138=5\x01151=5\x0114=0\x016=0\x0110=222\x01")
    with pytest.raises(fx.FixError) as e:
        fx.decode(m)
    assert e.value.kind == "order"
