"""Write firm.fixengine's golden fixtures (synthetic; the broker side is scripted here).

data/wikipedia_example.fix  the FIX 4.2 logon whose body length (65) and checksum (062) are published
data/conversation.txt       a session day in miniature: logon, an order and its reports, a lost report and a lost
                            heartbeat (gap, resend request, resend with PossDup and a gap fill), the broker asking us
                            to resend (we gap-fill our heartbeat and resend our cancel), a silent broker (test
                            request, answered), logout
data/expected_trace.txt     the Python reference's trace of that conversation: the C++ engine must reproduce it
"""
import pathlib

import firm_fixengine as fx

HERE = pathlib.Path(__file__).resolve().parent


def broker(msg_type, body, seq, now, header=()):
    raw = fx.encode(msg_type, body, seq, "BROKER", "FIRM", now, header=header)
    return f"{now} in {raw.replace(fx.SOH, b'|').decode()}"


def main():
    data = HERE / "data"
    data.mkdir(exist_ok=True)
    (data / "wikipedia_example.fix").write_text(
        "8=FIX.4.2|9=65|35=A|49=SERVER|56=CLIENT|34=177|52=20090107-18:15:16|98=0|108=30|10=062|\n")
    order = "11=ORD1|55=ESZ6|54=1|38=5|40=2|44=5723.25|59=0|60=20260925-14:30:01.000"
    new = [(37, "X1"), (11, "ORD1"), (17, "E1"), (150, "0"), (39, "0"), (55, "ESZ6"), (54, "1"), (38, 5), (151, 5),
           (14, 0), (6, 0)]
    part = [(37, "X1"), (11, "ORD1"), (17, "E2"), (150, "F"), (39, "1"), (55, "ESZ6"), (54, "1"), (38, 5), (32, 2),
            (31, "5723.25"), (151, 3), (14, 2), (6, "5723.25")]
    fill = [(37, "X1"), (11, "ORD1"), (17, "E3"), (150, "F"), (39, "2"), (55, "ESZ6"), (54, "1"), (38, 5), (32, 3),
            (31, "5723.25"), (151, 0), (14, 5), (6, "5723.25")]
    t0 = 52_200_000                                     # 14:30:00.000
    ev = [
        "# our side is FIRM; lines 'in' come from BROKER; times in ms from midnight UTC",
        f"{t0} logon",
        broker(b"A", [(98, 0), (108, 30)], 1, t0 + 5),
        f"{t0 + 1000} send D {order}",
        broker(b"8", new, 2, t0 + 1002),
        broker(b"0", [], 3, t0 + 31_000),
        "# seq 4 (the partial fill) and seq 5 (a heartbeat) are lost on the way",
        broker(b"8", fill, 6, t0 + 61_500),
        "# the broker answers our resend request: seq 4 again, a gap fill for its heartbeat, seq 6 again",
        broker(b"8", part, 4, t0 + 61_510, header=[(43, "Y"), (122, fx.sending_time(t0 + 45_000))]),
        broker(b"4", [(123, "Y"), (36, 6)], 5, t0 + 61_510, header=[(43, "Y")]),
        broker(b"8", fill, 6, t0 + 61_511, header=[(43, "Y"), (122, fx.sending_time(t0 + 61_500))]),
        f"{t0 + 62_000} timer",
        f"{t0 + 70_000} send F 41=ORD1|11=ORD2|55=ESZ6|54=1|38=5|60=20260925-14:31:10.000",
        "# the broker missed everything from our seq 3 on",
        broker(b"2", [(7, 3), (16, 0)], 7, t0 + 70_100),
        "# then it falls silent: heartbeat interval 30 s, test request after 36 s of silence",
        f"{t0 + 100_200} timer",
        f"{t0 + 106_200} timer",
        broker(b"0", [(112, "TEST1")], 8, t0 + 106_250),
        f"{t0 + 120_000} logout",
        broker(b"5", [], 9, t0 + 120_020),
    ]
    (data / "conversation.txt").write_text("\n".join(ev) + "\n")
    s = fx.replay(ev)
    (data / "expected_trace.txt").write_text("\n".join(s.trace) + "\n")


if __name__ == "__main__":
    main()
