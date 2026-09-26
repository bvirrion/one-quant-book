"""Write the shared fixtures of firm.exchsim (data/): the engine journal every engine replays, the outputs it must
reproduce byte for byte, golden decoded CSVs for client codecs, MoldUDP64 and SoupBinTCP samples, and schema.json.

    .venv/bin/python code/firm/exchsim/make_fixtures.py

Files:
    fixture_config.json      the engine configuration (two instruments: price-time and top-order pro rata)
    fixture_journal.bin      journal records (t_ns u64 | session u16 | length u16 | message): four minutes of Book 7's
                             tape flow plus a chaos agent sending every message type, and every control
    fixture_out.bin          per record: u32 index | u16 feed count | u16 report count | (u16 len | feed message)*
                             | (u16 session | u16 len | report)*; then per instrument u32 0xFFFFFFFF | u16 locate
                             | u16 n | (u16 len | message)*: the final snapshot (seq = feed messages so far)
    fixture_out.sha256       SHA-256 of fixture_out.bin
    golden/feed_<T>.csv, golden/in_<T>.csv, golden/out_<T>.csv, golden/ctl_<T>.csv   every message of the fixture,
                             decoded, one CSV per protocol and type (byte offset in its file first)
    golden/feed.bin, golden/in.bin, golden/out.bin, golden/ctl.bin   the same messages framed (u16 len | bytes);
                             at most the first 300 messages of each type
    fixture_mold.bin         the first 200 MoldUDP64 packets of the fixture day as a recorded file
    fixture_soup.bin, fixture_soup.csv   a SoupBinTCP conversation (login, orders, reports, heartbeats, logout)
    ../schema.json           every message of every protocol (generated from firm_exchsim_codec.MESSAGES)
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import struct
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "tape"))
from firm_exchsim import (  # noqa: E402
    SEC,
    Agent,
    ExchangeConfig,
    FeeSchedule,
    InstrumentSpec,
    LatencyModel,
    Order,
    Phases,
    SessionSpec,
    Simulator,
    TapeBackground,
    Throttle,
)
from firm_exchsim_codec import NT, encode, file_record, journal_parse, schema, soup_encode  # noqa: E402
from firm_exchsim_engine import Engine  # noqa: E402
from firm_tape import TapeConfig  # noqa: E402

DATA = HERE / "data"
OPEN = 34_200 * SEC
C = NT["ctl"]


def config() -> ExchangeConfig:
    inst = (InstrumentSpec("SIM1", 1, tick=100, lot=100, start_price=1_000_000),
            InstrumentSpec("FUT1", 2, tick=2500, lot=1, start_price=50_000_000, matching="configurable",
                           alloc={"top_pct": 40, "fifo_pct": 20, "min_alloc": 2}))
    ph = Phases(start_ns=OPEN - 40 * SEC, open_ns=OPEN, close_ns=OPEN + 240 * SEC, end_ns=OPEN + 260 * SEC,
                open_auction=True, preopen_ns=OPEN - 30 * SEC, close_auction=True, indicative_every_ns=10 * SEC,
                moc_cutoff_ns=OPEN + 220 * SEC)
    return ExchangeConfig(venue="SIMX", instruments=inst, fees=FeeSchedule(-0.0020, 0.0030, 0.0005), phases=ph,
                          throttle=Throttle(rate=200, burst=20), engine_ns=700, seed=11)


class Chaos(Agent):
    """Sends every kind of message, near the market, at random: the fixture's coverage generator."""

    name = "chaos"

    def __init__(self, seed: int, stp_group: int = 3):
        self.rng = np.random.default_rng(seed)
        self.g = stp_group

    def on_start(self, ctx):
        ctx.set_timer(OPEN - 25 * SEC - ctx.now_ns + int(self.rng.integers(1, 40)) * 10_000_000, "go")

    def _px(self, ctx, loc):
        tick = 100 if loc == 1 else 2500
        ref = 1_000_000 if loc == 1 else 50_000_000
        b, _, a, _ = ctx.top(loc)
        mid = ((b or ref) + (a or ref)) // 2
        return (mid // tick + int(self.rng.integers(-4, 5))) * tick

    def on_timer(self, ctx, tag):
        r = self.rng
        loc = int(r.choice([1, 2], p=[0.6, 0.4]))
        side = "B" if r.random() < 0.5 else "S"
        u = r.random()
        live = [o for o in ctx.working() if o["status"] == "live"]
        if u < 0.45 or not live:
            disp = r.choice(list("YYYYYNMP"))
            tif = r.choice(list("DDDDGIF")) if disp in "YN" else "D"
            qty = int(r.integers(1, 8)) * (100 if loc == 1 else 1)
            px = self._px(ctx, loc) if r.random() > 0.08 else 0
            dq = int(qty // 2) if disp == "Y" and r.random() < 0.15 and qty > 1 else 0
            mq = int(qty // 2) if (disp == "M" or tif == "I") and r.random() < 0.3 else 0
            stop = 0
            if r.random() < 0.05 and disp in "YN":
                stop = self._px(ctx, loc)
            ctx.send(Order(loc, side, qty, px if disp in "YN" or r.random() < 0.5 else 0, tif, disp,
                           post_only=bool(r.random() < 0.1), display_qty=dq, min_qty=mq,
                           stp_group=self.g if r.random() < 0.3 else 0,
                           stp_mode=str(r.choice(list("NOWBD"))), stop_price=stop))
        elif u < 0.65:
            o = live[int(r.integers(len(live)))]
            ctx.cancel(o["cl"], int(o["leaves"] // 2) if r.random() < 0.3 else 0)
        elif u < 0.85:
            o = live[int(r.integers(len(live)))]
            tick = 100 if o["locate"] == 1 else 2500
            same = r.random() < 0.5
            px = o["price"] if same or o["price"] == 0 else o["price"] + int(r.integers(-2, 3)) * tick
            qty = max(1, int(o["leaves"]) + int(r.integers(-2, 3)) * (100 if o["locate"] == 1 else 1))
            ctx.replace(o["cl"], qty, px)
        elif u < 0.93:
            b = self._px(ctx, loc)
            tick = 100 if loc == 1 else 2500
            ctx.quote(loc, b - tick, int(r.integers(0, 4)) * (100 if loc == 1 else 1), b + tick,
                      int(r.integers(1, 4)) * (100 if loc == 1 else 1))
        elif u < 0.96:
            ctx.mass_cancel(int(r.choice([0, 1, 2])), str(r.choice(list("BS*"))))
        else:
            for _ in range(int(r.integers(5, 30))):                 # a burst: exercises the throttle
                ctx.send(Order(loc, side, 100 if loc == 1 else 1, self._px(ctx, loc), "I"))
        if ctx.now_ns < OPEN + 250 * SEC:
            ctx.set_timer(int(r.exponential(120_000_000)) + 1, "go")


def build():
    cfg = config()
    sim = Simulator(cfg, seed=11)
    sim.add_background(TapeBackground(TapeConfig(seconds=240.0, seed=21, news_at=120.0, news_len=20.0),
                                      start_ns=OPEN))
    sim.add_agent(Chaos(1), SessionSpec(firm="HF1", latency=LatencyModel(40_000, 40_000, 30_000, 0.3)))
    sim.add_agent(Chaos(2), SessionSpec(firm="HF1", latency=LatencyModel(80_000, 80_000, 60_000, 0.5)))
    sim.add_agent(Chaos(3, stp_group=0), SessionSpec(firm="HF2", latency=LatencyModel(20_000, 20_000, 20_000)))
    ctl = [(OPEN + 30 * SEC, "SIMX", C["R"](1, 1_000_000, 950_000, 1_050_000)),
           (OPEN + 50 * SEC, "SIMX", C["P"](2, "H", "HALT")),
           (OPEN + 60 * SEC, "SIMX", C["P"](2, "U", "REOP")),
           (OPEN + 65 * SEC, "SIMX", C["I"](2, "H")),
           (OPEN + 70 * SEC, "SIMX", C["P"](2, "T", "RESM")),
           (OPEN + 100 * SEC, "SIMX", C["P"](2, "B", "FBA ")),
           (OPEN + 140 * SEC, "SIMX", C["P"](2, "T", "CONT")),
           (OPEN + 160 * SEC, "SIMX", C["D"](3)),
           (OPEN + 165 * SEC, "SIMX", C["L"](3, 2, "Y")),
           (OPEN + 180 * SEC, "SIMX", C["R"](1, 1_000_000, 0, 0)),
           (OPEN + 190 * SEC, "SIMX", C["N"](1, 999_900, 1_000_300)),     # a reference quote for midpoint pegs
           (OPEN + 205 * SEC, "SIMX", C["N"](1, 1_000_100, 1_000_200)),
           (OPEN + 215 * SEC, "SIMX", C["N"](1, 0, 0))]
    ctl += [(OPEN + 100 * SEC + k * 4 * SEC, "SIMX", C["X"](2, "B")) for k in range(1, 10)]
    IN = NT["in"]
    bad = [IN["O"](9001, 1, "B", 100, 999_950, "D", "Y", "N", 0, 0, 0, "N", 0),     # off the tick grid: J X
           IN["O"](9002, 1, "B", 0, 999_900, "D", "Y", "N", 0, 0, 0, "N", 0),       # zero quantity: J Q
           IN["O"](9003, 7, "B", 100, 999_900, "D", "Y", "N", 0, 0, 0, "N", 0),     # unknown instrument: J S
           IN["O"](9004, 1, "B", 100, 1_100_000, "D", "Y", "N", 0, 0, 0, "N", 0),   # outside the band: J B
           IN["O"](9005, 1, "S", 100, 0, "O", "Y", "N", 0, 0, 0, "N", 0),           # at-the-open in continuous: J H
           IN["X"](424242, 0), IN["U"](424242, 424243, 100, 999_900),                  # unknown order: J L
           IN["O"](9006, 2, "B", 3, 50_000_000, "D", "Y", "N", 0, 0, 0, "N", 0)]    # a resting futures bid
    orders = [(OPEN + 40 * SEC + k * SEC, "SIMX", m) for k, m in enumerate(bad)]
    cutoff = IN["O"](9007, 1, "B", 100, 0, "C", "Y", "N", 0, 0, 0, "N", 0)            # after the cut-off: J C
    orders += [(OPEN + 230 * SEC, "SIMX", cutoff)]
    orders += [(OPEN + 200 * SEC, "SIMX", IN["O"](9008 + k, 1, "B" if k % 2 else "S", 100 * (k + 1),
                                               0 if k < 2 else 1_000_000, "C", "Y", "N", 0, 0, 0, "N", 0))
               for k in range(4)]                                                  # at-the-close orders
    sim.add_events(controls=ctl, orders=orders)
    return sim.run()


def replay(journal: bytes, cfg: dict) -> bytes:
    e = Engine(cfg)
    out = []
    recs = journal_parse(journal)
    feed_n = 0
    for i, (t, s, p) in enumerate(recs):
        feed, reps = e.process_bytes(t, s, p)
        feed_n += len(feed)
        fb = b"".join(struct.pack(">H", len(x)) + x for x in (encode("feed", m) for m in feed))
        rb = b"".join(struct.pack(">HH", ss, len(x)) + x for ss, x in ((ss, encode("out", r)) for ss, r in reps))
        out.append(struct.pack(">IHH", i, len(feed), len(reps)) + fb + rb)
    for loc in sorted(e.inst):
        snap = [encode("feed", m) for m in e.snapshot(loc, feed_n)]
        out.append(struct.pack(">IHH", 0xFFFFFFFF, loc, len(snap)) + b"".join(struct.pack(">H", len(x)) + x
                                                                               for x in snap))
    return b"".join(out)


def golden(res, journal: bytes) -> None:
    g = DATA / "golden"
    g.mkdir(exist_ok=True)
    from firm_exchsim_codec import decode
    streams = {"feed": [encode("feed", m) for _, _, m in res.feed_messages()],
               "in": [], "ctl": [], "out": []}
    for _, s, p in journal_parse(journal):
        streams["ctl" if s == 0 else "in"].append(p)
    for (vi, sid), _ in sorted(res.sim.sessions.items()):
        for r in res.sim.venues[vi].reports.get(sid, []):
            streams["out"].append(encode("out", r))
    for proto, msgs in streams.items():
        blob, rows, off = b"", {}, 0
        for b in msgs:
            m = decode(proto, b)
            t = type(m).__name__[-1]
            if len(rows.get(t, ())) >= 300:
                continue
            rows.setdefault(t, []).append((off, m))
            blob += struct.pack(">H", len(b)) + b
            off += 2 + len(b)
        (g / f"{proto}.bin").write_bytes(blob)
        for t, lst in rows.items():
            name = {"+": "plus"}.get(t, t)
            head = "offset," + ",".join(lst[0][1]._fields)
            lines = [head] + [f"{o}," + ",".join(str(x) for x in m) for o, m in lst]
            (g / f"{proto}_{name}.csv").write_text("\n".join(lines) + "\n")


def soup_sample() -> None:
    sc, ss, i_, o_ = NT["soup_client"], NT["soup_server"], NT["in"], NT["out"]
    conv = [("C", sc["L"]("HF1", "secret", "", 1)), ("S", ss["A"]("SIMX", 1)),
            ("C", sc["U"](encode("in", i_["O"](1, 1, "B", 100, 999_900, "D", "Y", "N", 0, 0, 0, "N", 0)))),
            ("S", ss["S"](encode("out", o_["A"](OPEN + 5, 1, 7, 1, "B", 100, 999_900, "D", "Y", "L")))),
            ("C", sc["R"]()), ("S", ss["H"]()),
            ("C", sc["U"](encode("in", i_["X"](1, 0)))),
            ("S", ss["S"](encode("out", o_["C"](OPEN + 9, 1, 100, "U")))),
            ("C", sc["O"]()), ("S", ss["Z"]())]
    blob, lines = b"", ["direction,offset,type,hex"]
    for d, m in conv:
        b = soup_encode("soup_client" if d == "C" else "soup_server", m)
        lines.append(f"{d},{len(blob)},{b[2:3].decode()},{b.hex()}")
        blob += b
    (DATA / "fixture_soup.bin").write_bytes(blob)
    (DATA / "fixture_soup.csv").write_text("\n".join(lines) + "\n")


def main() -> None:
    DATA.mkdir(exist_ok=True)
    res = build()
    cfg = config().engine_config()
    journal = res.journal_bytes()
    (DATA / "fixture_config.json").write_text(json.dumps(cfg, indent=1) + "\n")
    (DATA / "fixture_journal.bin").write_bytes(journal)
    out = replay(journal, cfg)
    (DATA / "fixture_out.bin").write_bytes(out)
    (DATA / "fixture_out.sha256").write_text(hashlib.sha256(out).hexdigest() + "\n")
    (DATA / "fixture_mold.bin").write_bytes(b"".join(file_record(t, p) for t, p in res.packets()[:200]))
    golden(res, journal)
    soup_sample()
    (HERE / "schema.json").write_text(json.dumps(schema(), indent=1) + "\n")
    e = res.engine()
    kinds: dict[str, int] = {}
    for _, _, m in res.feed_messages():
        k = type(m).__name__[-1]
        kinds[k] = kinds.get(k, 0) + 1
    rk: dict[str, int] = {}
    for v in res.sim.venues:
        for reps in v.reports.values():
            for r in reps:
                k = type(r).__name__[-1] + getattr(r, "reason", "")
                rk[k] = rk.get(k, 0) + 1
    print(len(journal_parse(journal)), "records,", len(e.trades), "executions; feed", kinds, "; reports", rk)


if __name__ == "__main__":
    main()
