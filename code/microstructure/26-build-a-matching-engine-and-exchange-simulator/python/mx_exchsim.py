"""One Quant Book 10, chapter 26: the exchange simulator, exercised.

    scenario()          a client's session in process: seven orders and the reports they bring back
    recovery(seconds, lossy_a)   ten minutes of Book 7's tape flow through the venue with a lossy line A (bursts,
                        unless lossy_a is False) and an outage on line B: messages lost on each line, after
                        arbitrating the two lines, after the retransmission service; and a snapshot plus the
                        incremental feed rebuilding the book
    determinism()       the same inputs twice (SHA-256 of the feed and the journal); the Python engine replaying the
                        shared fixture against its stored SHA-256
    throughput()        the fixture's journal records a second through the Python engine and through the C++20 engine's
                        test program (built if needed), measured on this laptop
All deterministic except the timings.
"""
from __future__ import annotations

import functools
import hashlib
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[4]
EX = ROOT / "code" / "firm" / "exchsim"
for c in ("exchsim", "tape", "lob"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_exchsim import (  # noqa: E402
    SEC,
    Agent,
    ExchangeConfig,
    FeedConfig,
    Order,
    Phases,
    SessionSpec,
    Simulator,
    TapeBackground,
)
from firm_exchsim_codec import file_parse, journal_parse, mold_parse  # noqa: E402
from firm_exchsim_engine import Engine  # noqa: E402
from firm_lob import MessageBook  # noqa: E402
from firm_tape import TapeConfig  # noqa: E402

OPEN = 34_200 * SEC


def venue(seconds: float, **kw) -> ExchangeConfig:
    return ExchangeConfig(phases=Phases(start_ns=OPEN - SEC, open_ns=OPEN, close_ns=OPEN + int(seconds * SEC),
                                        end_ns=OPEN + int((seconds + 1) * SEC)), **kw)


class Client(Agent):
    """Sends a scripted list of (seconds after the open, action) and keeps every report."""

    name = "client"

    def __init__(self, script):
        self.script, self.reports = script, []

    def on_start(self, ctx):
        for i, (t, _) in enumerate(self.script):
            ctx.set_timer(OPEN + int(t * SEC) - ctx.now_ns, i)

    def on_timer(self, ctx, i):
        kind, arg = self.script[i][1]
        if kind == "send":
            ctx.send(arg)
        else:
            ctx.cancel(arg)

    def on_report(self, ctx, rep):
        self.reports.append((round((ctx.now_ns - OPEN) / SEC, 3), type(rep).__name__[-1], getattr(rep, "cl_ord_id", 0),
                             getattr(rep, "qty", getattr(rep, "decrement", 0)), getattr(rep, "reason", "")))


SCRIPT = ((1.0, ("send", Order(side="B", qty=300, price=1_000_000, cl_ord_id=1))),          # rests at 100.00
          (2.0, ("send", Order(side="S", qty=100, price=1_000_000, cl_ord_id=2))),          # crosses its own bid
          (3.0, ("send", Order(side="S", qty=500, price=999_900, tif="I", cl_ord_id=3))),   # IOC: fills 200, rest out
          (4.0, ("send", Order(side="B", qty=200, price=1_000_200, post_only=True, cl_ord_id=4))),
          (5.0, ("send", Order(side="S", qty=100, price=1_000_100, cl_ord_id=5))),
          (6.0, ("send", Order(side="B", qty=100, price=1_000_150, cl_ord_id=6))),          # off the tick grid
          (7.0, ("cancel", 5)))


@functools.cache
def scenario() -> list:
    sim = Simulator(venue(10.0), seed=1)
    c = Client(SCRIPT)
    sim.add_agent(c, SessionSpec(firm="CLI"))
    sim.run()
    return c.reports


def _tape_day(seconds: float, feed: FeedConfig):
    sim = Simulator(venue(seconds, feed=feed), seed=3)
    sim.add_background(TapeBackground(TapeConfig(seconds=seconds, seed=7, news_at=None)))
    return sim.run()


@functools.cache
def recovery(seconds: float = 600.0, lossy_a: bool = True) -> dict:
    feed = FeedConfig(burst_loss=(0.02, 0.3, 0.9) if lossy_a else None,
                      outages=(("B", OPEN + 60 * SEC, OPEN + 70 * SEC),), snapshot_every_ns=30 * SEC)
    res = _tape_day(seconds, feed)
    ideal = [mold_parse(p) for _, p in res.packets()]
    data = [(s, c, m) for _, s, c, m in ideal if c not in (0, 0xFFFF)]
    last = max(s + c - 1 for s, c, _ in data)
    got, per_line = {}, {}
    for line in ("A", "B"):
        seen = set()
        for _, p in file_parse(res.recorded(line=line)):
            _, s, c, msgs = mold_parse(p)
            if c not in (0, 0xFFFF):
                for k, m in enumerate(msgs):
                    seen.add(s + k)
                    got[s + k] = m
        per_line[line] = last - len(seen)
    gaps = [s for s in range(1, last + 1) if s not in got]
    requests = 0
    for s in gaps:
        pk = res.retransmit("", s, 1)
        requests += 1
        got[s] = mold_parse(pk[0])[3][0]
    # snapshot recovery: the snapshot in the middle of the day plus the incremental feed after it
    t, _, seq, msgs = res.sim.venues[0].snaps[len(res.sim.venues[0].snaps) // 2]
    book = MessageBook()
    for m in msgs:
        if type(m).__name__ == "Feed_A":
            book.apply("A", m.ref, 1 if m.side == "B" else -1, m.price, m.shares)
    for _, s, m in res.feed_messages():
        k = type(m).__name__[-1]
        if s <= seq or k not in "AEXDUC":
            continue
        if k == "A":
            book.apply("A", m.ref, 1 if m.side == "B" else -1, m.price, m.shares)
        elif k in "EXC":
            book.apply("X", m.ref, qty=m.shares)
        elif k == "D":
            book.apply("D", m.ref)
        else:
            book.apply("U", m.ref, price=m.price, qty=m.shares, new_ref=m.new_ref)
    eng = res.engine().book(1)
    return {"messages": last, "packets": len(data), "lost_a": per_line["A"], "lost_b": per_line["B"],
            "after_arbitration": len(gaps), "retransmit_requests": requests,
            "complete": all(s in got for s in range(1, last + 1)),
            "snapshot_ok": book.depth(1, 10) == eng.depth(1, 10) and book.depth(-1, 10) == eng.depth(-1, 10),
            "snapshots": len(res.sim.venues[0].snaps)}


@functools.cache
def determinism() -> dict:
    feed = FeedConfig(burst_loss=(0.02, 0.3, 0.9))
    a, b = _tape_day(120.0, feed), _tape_day(120.0, feed)
    h = [hashlib.sha256(r.feed_bytes(line="A") + r.journal_bytes()).hexdigest() for r in (a, b)]
    sys.path.insert(0, str(EX))
    import make_fixtures
    cfg = json.loads((EX / "data" / "fixture_config.json").read_text())
    out = make_fixtures.replay((EX / "data" / "fixture_journal.bin").read_bytes(), cfg)
    return {"same": h[0] == h[1], "sha": h[0][:12],
            "fixture_ok": hashlib.sha256(out).hexdigest() == (EX / "data" / "fixture_out.sha256").read_text().strip(),
            "records": len(journal_parse((EX / "data" / "fixture_journal.bin").read_bytes()))}


def throughput() -> dict:
    cfg = json.loads((EX / "data" / "fixture_config.json").read_text())
    recs = journal_parse((EX / "data" / "fixture_journal.bin").read_bytes())
    t = time.perf_counter()
    e = Engine(cfg)
    for ts, s, p in recs:
        e.process_bytes(ts, s, p)
    py = len(recs) / (time.perf_counter() - t)
    exe = EX / "cpp" / "bin" / "exchsim_engine_test"
    newest = max(f.stat().st_mtime for f in (EX / "cpp").glob("*.[ch]pp"))
    if not exe.exists() or exe.stat().st_mtime < newest:                  # as tools/test_code.sh builds it
        exe.parent.mkdir(exist_ok=True)
        subprocess.run(["g++", "-std=c++20", "-O2", "-I", "code/firm/exchsim/cpp",
                        "code/firm/exchsim/cpp/exchsim_engine_test.cpp", "-o", str(exe)], check=True, cwd=str(ROOT))
    t = time.perf_counter()
    run = subprocess.run([str(exe)], capture_output=True, text=True, cwd=str(ROOT), check=True)
    cpp = len(recs) / (time.perf_counter() - t)
    return {"python": py, "cpp": cpp, "cpp_out": run.stdout.strip().splitlines()}
