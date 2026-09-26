"""Chapter 15 -- the session trace in short form, and the arithmetic of a gap: how many messages a counterparty
must resend after a disconnect, with and without gap fill of administrative messages, and how long resynchronising
takes."""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/fixengine"))
import firm_fixengine as fx  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parents[1]
NAMES = {"A": "Logon", "0": "Heartbeat", "1": "TestRequest", "2": "ResendRequest", "4": "SequenceReset", "5": "Logout",
         "D": "NewOrderSingle", "8": "ExecutionReport", "F": "OrderCancelRequest"}
KEEP = (43, 7, 16, 123, 36, 112, 39)


def short(line):
    """'52261500 out 8=FIX.4.4|...' -> '14:31:01.500 FIRM  -> ResendRequest(2) seq 3  7=4 16=0'."""
    now, verb, rest = line.split(" ", 2)
    ms = int(now)
    t = f"{ms // 3_600_000:02d}:{ms // 60_000 % 60:02d}:{ms // 1000 % 60:02d}.{ms % 1000:03d}"
    if verb not in ("in", "out"):
        return f"{t}          {verb} {rest}"
    m = fx.decode(rest.encode().replace(b"|", fx.SOH))
    typ = m.msg_type.decode()
    extra = " ".join(f"{k}={m.get(k).decode()}" for k in KEEP if m.get(k) is not None)
    arrow = "FIRM   ->" if verb == "out" else "BROKER ->"
    return f"{t} {arrow} {NAMES.get(typ, typ)}({typ}) seq {m.seq}  {extra}".rstrip()


def write_short_trace():
    lines = (ROOT / "code/firm/fixengine/data/expected_trace.txt").read_text().splitlines()
    out = HERE / "python/trace_short.txt"
    out.write_text("\n".join(short(x) for x in lines) + "\n")
    return out


def detection_s(hb_s):
    """Silence after which the build's session gives up: a test request after 1.2 intervals, then one more."""
    return 2.2 * hb_s


def sender_stream(rate, seconds, hb_s, seed=1):
    """Message types a sender produces over `seconds`: application messages at Poisson `rate`, and a heartbeat
    whenever `hb_s` seconds pass without any message sent."""
    rng = np.random.default_rng(seed)
    t, last, out = 0.0, 0.0, []
    while True:
        gap = rng.exponential(1 / rate) if rate > 0 else np.inf
        while last + hb_s <= min(t + gap, seconds):
            last += hb_s
            out.append("0")
        t += gap
        if t > seconds:
            return out
        out.append("8")
        last = t


def resend_count(types, gap_fill=True):
    """Messages on the wire to answer a resend request covering `types`: application messages resent one by one,
    and either one SequenceReset-GapFill per run of administrative messages or every administrative message."""
    app = sum(1 for x in types if x not in ("0", "1", "2", "4", "5", "A"))
    if not gap_fill:
        return len(types)
    runs = sum(1 for i, x in enumerate(types) if x == "0" and (i == 0 or types[i - 1] != "0"))
    return app + runs


def resync_s(n, msg_bytes, bandwidth_bps, per_msg_s, rtt_s):
    """Logon and resend request round trip, then the resent messages on the wire and through the receiver."""
    return 2 * rtt_s + n * msg_bytes * 8 / bandwidth_bps + n * per_msg_s


if __name__ == "__main__":
    print(write_short_trace().read_text())
