"""Write the deterministic binary sample shared by the Python, C++ and Rust tests."""
import pathlib
import random

from firm_feed import Msg, encode

OUT = pathlib.Path(__file__).resolve().parent / "data/sample.itch"


def build(n_events: int = 2000, seed: int = 28) -> bytes:
    rng = random.Random(seed)
    ts, ref, match = 34_200_000_000_000, 1000, 1            # 09:30:00
    live: dict[int, tuple[str, int, int]] = {}
    mid = 1_000_000                                          # $100.0000
    out = bytearray()
    for _ in range(n_events):
        ts += rng.randint(1_000, 5_000_000)
        u = rng.random()
        if u < 0.55 or len(live) < 20:
            ref += 1
            side = rng.choice("BS")
            off = rng.randint(1, 12) * 100
            price = mid - off if side == "B" else mid + off
            shares = rng.choice((100, 100, 200, 300, 500))
            live[ref] = (side, shares, price)
            out += encode(Msg("A", 7, 0, ts, ref, side, shares, "XYZ", price))
        else:
            if u < 0.70:                                     # an execution hits the oldest order at the best price
                want = rng.choice("BS")
                side_refs = [k for k, v in live.items() if v[0] == want] or list(live)
                best = (max if live[side_refs[0]][0] == "B" else min)(live[k][2] for k in side_refs)
                r = min(k for k in side_refs if live[k][2] == best)
            else:
                r = rng.choice(list(live))
            side, shares, price = live[r]
            if u < 0.70:
                q = rng.choice((100, shares))
                q = min(q, shares)
                out += encode(Msg("E", 7, 0, ts, r, shares=q, match=match))
                match += 1
                shares -= q
            elif u < 0.80 and shares > 100:
                out += encode(Msg("X", 7, 0, ts, r, shares=100))
                shares -= 100
            else:
                out += encode(Msg("D", 7, 0, ts, r))
                shares = 0
            if shares == 0:
                del live[r]
            else:
                live[r] = (side, shares, price)
        if rng.random() < 0.01:
            out += encode(Msg("P", 7, 0, ts, 0, "B", 100, "XYZ", mid, match))
            match += 1
    return bytes(out)


if __name__ == "__main__":
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_bytes(build())
    print(OUT, OUT.stat().st_size, "bytes")
