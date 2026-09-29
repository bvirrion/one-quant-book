"""Write data/packets.bin (two seconds of the exchange simulator's feed from the open, one instrument; length-prefixed
MoldUDP64 packets) and data/expected.txt (the Python cycle model's orders and rejects for the chapter's settings),
shared by the Python, C++20, Verilator and Icarus tests. Deterministic: the simulator is seeded."""
import dataclasses
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
for c in ("exchsim", "tape"):
    sys.path.insert(0, str(HERE.parent / c))
import firm_hwtrade as hw  # noqa: E402

SEC = 1_000_000_000
OPEN = 34_200 * SEC
SETTINGS = ((1_000_200, 10_000, -1), (1_000_300, 10_000, -1), (1_000_300, 600, -1), (1_000_300, 10_000, 3000))


def packets(seconds=2.0):
    from firm_exchsim import ExchangeConfig, FeedConfig, Simulator, TapeBackground
    from firm_tape import TapeConfig
    sim = Simulator(dataclasses.replace(ExchangeConfig(), feed=FeedConfig()), seed=1)
    sim.add_background(TapeBackground(TapeConfig(seconds=seconds, seed=7, lo_rate=40.0, in_spread=40.0, noise_mu=6.0,
                                                 cancel=0.5, news_at=None)))
    res = sim.run(until_ns=OPEN + int(seconds * SEC) + SEC // 2)
    return [p for _, p in res.packets()]


def load(path=HERE / "data" / "packets.bin"):
    b, out, off = pathlib.Path(path).read_bytes(), [], 0
    while off < len(b):
        n = struct.unpack_from(">I", b, off)[0]
        out.append(b[off + 4:off + 4 + n])
        off += 4 + n
    return out


def main():
    pk = packets()
    (HERE / "data" / "packets.bin").write_bytes(b"".join(struct.pack(">I", len(p)) + p for p in pk))
    beats = hw.beats_of(pk)
    lines = ["# thresh max_qty kill_at orders rejects first_order_cycle order_digest"]
    for thresh, maxq, kill in SETTINGS:
        orders, rej = hw.CycleModel().run(beats, thresh, maxq, kill)
        digest = sum((i + 1) * (c * 7 + q * 13 + p) for i, (c, _, q, p) in enumerate(orders)) % (1 << 61)
        first = orders[0][0] if orders else -1
        lines.append(f"{thresh} {maxq} {kill} {len(orders)} {rej} {first} {digest}")
    (HERE / "data" / "expected.txt").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
