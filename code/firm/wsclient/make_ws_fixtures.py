"""Write firm.wsclient's fixtures (synthetic, in the shape a large venue documents for its diff depth stream).

data/depth_updates.jsonl   1,000 depth updates: {"e":"depthUpdate","E":ms,"s":"BTCUSDT","U":first,"u":last,
                           "b":[["price","qty"],...],"a":[...]}, prices with 2 decimals, quantities with up to 5
data/depth_expected.txt    the Python reference's decoding: "E s U u|p:q,p:q|p:q,..." at 1e-8
data/frames.bin            a server-to-client byte stream: the first 50 updates as text frames (some fragmented in
                           three), with pings in between, then a close frame
data/frames_expected.txt   the messages the reassembler delivers: "<opcode> <payload hex>"
"""
import json
import pathlib
import random

import firm_wsclient as ws

HERE = pathlib.Path(__file__).resolve().parent


def updates(n=1000, seed=3):
    rng = random.Random(seed)
    mid, uid, t = 6_412_345, 1_000_000, 1_758_800_000_000
    out = []
    for _ in range(n):
        mid += rng.choice((-2, -1, 0, 0, 1, 2))
        k = rng.randint(1, 5)
        first, uid = uid + 1, uid + k
        t += rng.randint(1, 100)

        def side(sign, mid=mid):
            levels = []
            for _ in range(rng.randint(0, 10)):
                px = mid + sign * rng.randint(1, 40)
                qty = rng.choice([0, rng.randint(1, 5_000_000)])
                levels.append([f"{px // 100}.{px % 100:02d}", f"{qty / 100000:.5f}".rstrip("0").rstrip(".")])
            return levels
        out.append({"e": "depthUpdate", "E": t, "s": "BTCUSDT", "U": first, "u": uid, "b": side(-1), "a": side(1)})
    return out


def line(d):
    lv = ["" if not x else ",".join(f"{p}:{q}" for p, q in x) for x in (d.bids, d.asks)]
    return f"{d.event_time} {d.symbol} {d.first} {d.last}|{lv[0]}|{lv[1]}"


def main():
    data = HERE / "data"
    data.mkdir(exist_ok=True)
    ups = updates()
    texts = [json.dumps(u, separators=(",", ":")) for u in ups]
    (data / "depth_updates.jsonl").write_text("\n".join(texts) + "\n")
    (data / "depth_expected.txt").write_text("\n".join(line(ws.decode_depth(x)) for x in texts) + "\n")
    rng = random.Random(5)
    stream, expected = b"", []
    for i, x in enumerate(texts[:50]):
        b = x.encode()
        if i % 7 == 3:                                        # fragmented in three, a ping between the fragments
            a, c = len(b) // 3, 2 * len(b) // 3
            stream += ws.encode_frame(b[:a], ws.OP_TEXT, fin=False)
            stream += ws.encode_frame(b"hb", ws.OP_PING)
            expected.append((ws.OP_PING, b"hb"))
            stream += ws.encode_frame(b[a:c], ws.OP_CONT, fin=False)
            stream += ws.encode_frame(b[c:], ws.OP_CONT, fin=True)
        else:
            stream += ws.encode_frame(b)
        expected.append((ws.OP_TEXT, b))
        if rng.random() < 0.1:
            stream += ws.encode_frame(b"", ws.OP_PING)
            expected.append((ws.OP_PING, b""))
    stream += ws.encode_frame(b"\x03\xe8", ws.OP_CLOSE)       # 1000: normal closure
    expected.append((ws.OP_CLOSE, b"\x03\xe8"))
    (data / "frames.bin").write_bytes(stream)
    (data / "frames_expected.txt").write_text("\n".join(f"{o} {p.hex()}" for o, p in expected) + "\n")


if __name__ == "__main__":
    main()
