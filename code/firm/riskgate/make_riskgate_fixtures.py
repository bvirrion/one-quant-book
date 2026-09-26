"""Write firm.riskgate's fixture: an event stream that exercises every check, at and around its boundaries, which the
C++ and Rust gates replay to the Python reference's decisions.

data/limits.json    two versions of the limits (the stream switches from 1 to 2 half-way)
data/events.txt     the events (format in firm_riskgate.replay)
data/expected.txt   "decisions <n> <fnv-1a 64 of the decision string> <counts>" and the decision string itself
"""
import json
import pathlib
import random

import firm_riskgate as rg

HERE = pathlib.Path(__file__).resolve().parent
TICK = 100


def fnv1a(s):
    h = 0xcbf29ce484222325
    for b in s.encode():
        h = ((h ^ b) * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return h


def limits():
    return {int(k): rg.Limits.from_dict(v) for k, v in json.loads((HERE / "data/limits.json").read_text()).items()}


def events(seed=5, n=12_000):
    rng = random.Random(seed)
    lim = limits()
    ev = []
    t = 1_000_000_000
    ref = {1: 1_000_000, 2: 250_000, 3: 1_500_000}
    ev.append(f"{t} L 1")
    for i, p in ref.items():
        ev.append(f"{t} P {i} {p}")
    # the boundaries first: collar (2% of 100.0000 = 20,000), quantity, notional, exactly at and one past each
    t += 1000
    ev += [f"{t} O 1 S1 1 B 100 1020000", f"{t + 1} O 2 S1 1 B 100 1020001", f"{t + 2} O 3 S1 1 S 100 980000",
           f"{t + 3} O 4 S1 1 S 100 979999", f"{t + 4} O 5 S3 2 B 500 250000", f"{t + 5} O 6 S3 2 B 501 250000",
           f"{t + 6} O 7 S3 3 B 1000 1500000", f"{t + 7} O 8 S3 3 B 1000 1500000",
           f"{t + 1_000_008} O 9 S3 3 B 1000 1500000"]
    for cl in range(1, 10):
        ev.append(f"{t + 1_000_010} X {cl}")
    t += 2_000_000
    cl = 100
    open_orders = []
    last_hb, last_ref = t, {i: t for i in ref}
    for k in range(n):
        t += int(rng.expovariate(1 / 150_000)) + 1
        if k == n // 2:
            ev.append(f"{t} L 2")
        if k == int(n * 0.3):                           # the risk service goes quiet for three seconds
            t += 3_000_000_000
            last_hb = t - 380_000_000                   # it comes back 20 ms later
            ev.append(f"{t - 1_000_000} O {cl} S1 1 B 100 {ref[1]}")    # refused: stale limits
            cl += 1
        if t - last_hb >= 400_000_000:
            ev.append(f"{t} H")
            last_hb = t
        for i in ref:
            if t - last_ref[i] >= 50_000_000 and not (i == 3 and int(n * 0.6) <= k < int(n * 0.7)):
                ref[i] = max(TICK * 10, ref[i] + TICK * rng.choice((-2, -1, 0, 1, 2)))
                ev.append(f"{t} P {i} {ref[i]}")
                last_ref[i] = t
        if k == int(n * 0.45):
            ev.append(f"{t} K strategy S2 cancel")
        if k == int(n * 0.5):
            ev.append(f"{t} U strategy S2")
        if k == int(n * 0.8):
            ev.append(f"{t} K firm - block")
        if k == int(n * 0.82):
            ev.append(f"{t} U firm -")
        r = rng.random()
        if r < 0.4:
            strat = rng.choice(("S1", "S1", "S2", "S3"))
            instr = rng.choice((1, 2, 3))
            side = rng.choice("BS")
            qty = rng.choice((100, 100, 100, 100, 200, 300, 500, 1000, 2000, 2500))
            band = ref[instr] * int(lim[1].instruments[instr]["collar_bp"]) // 10_000
            off = rng.choice((0, 0, 0, 0, TICK, TICK, 2 * TICK, -TICK, band, band + 1, 3 * band))
            price = ref[instr] + off if side == "B" else ref[instr] - off
            if rng.random() < 0.1 and open_orders:                 # repeat an earlier order: a duplicate
                _, strat, instr, side, qty, price = open_orders[-1]
            ev.append(f"{t} O {cl} {strat} {instr} {side} {qty} {price}")
            open_orders.append((cl, strat, instr, side, qty, price))
            cl += 1
        elif r < 0.75 and open_orders:
            j = rng.randrange(len(open_orders))
            o = open_orders[j]
            q = rng.choice((o[4], 100)) if o[4] > 100 else o[4]
            ev.append(f"{t} F {o[0]} {q} {o[5]}")
            if q == o[4]:
                open_orders.pop(j)
            else:
                open_orders[j] = (*o[:4], o[4] - q, o[5])
        elif open_orders:
            o = open_orders.pop(rng.randrange(len(open_orders)))
            ev.append(f"{t} X {o[0]}")
    return ev


def main():
    ev = events()
    (HERE / "data/events.txt").write_text("\n".join(ev) + "\n")
    g = rg.replay(ev, limits())
    s, counts = rg.decisions(g)
    c = ",".join(f"{k}:{v}" for k, v in counts.items())
    (HERE / "data/expected.txt").write_text(f"decisions {len(s)} {fnv1a(s):016x} {c}\n{s}\n")


if __name__ == "__main__":
    main()
