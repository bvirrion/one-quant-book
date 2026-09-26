"""Chapter 17 -- the budget of one websocket order, and the weekend problem's arithmetic: the share of the path from
the venue and back spent in the host's own processing, and what reusing a connection saves per order."""
import csv
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[4]
FIG = ROOT / "figdata/low-latency/17-websocket-rest-tls-and-json-at-speed"
STEPS = ("tls_open", "frame_decode", "json", "sign", "frame_encode", "tls_seal")


def read(name):
    with open(FIG / name, newline="", encoding="utf8") as f:
        return list(csv.DictReader(f))


def budget(path):
    """Microseconds per step of one order (receive the update, send the order) on the measured path."""
    r = next(x for x in read("measured_budget.csv") if x["path"] == path)
    return {k: float(r[k]) for k in STEPS}


def cpu_share(cpu_us, hop_us):
    """Share of the round trip venue -> host -> venue spent in the host's processing (two network hops)."""
    return cpu_us / (cpu_us + 2 * hop_us)


def new_connection_us(rtt_us, handshake_cpu_us, websocket_upgrade=False):
    """Opening a connection before a request: TCP (one round trip), TLS 1.3 (one round trip plus the handshake's
    computation), and for a websocket the HTTP upgrade (one more round trip)."""
    return (3 if websocket_upgrade else 2) * rtt_us + handshake_cpu_us


def masked_frame_bytes(payload):
    """Bytes on the wire of a client frame: 2-byte header, extended length, 4-byte mask key, payload."""
    ext = 0 if payload <= 125 else (2 if payload <= 0xFFFF else 8)
    return 2 + ext + 4 + payload


if __name__ == "__main__":
    for p in ("cpp", "python"):
        b = budget(p)
        print(p, round(sum(b.values()), 3), b)
