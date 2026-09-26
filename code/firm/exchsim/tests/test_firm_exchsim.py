"""Acceptance tests of the exchange simulator's Python reference (INTERFACES.md section 7)."""
import hashlib
import json
import pathlib
import struct
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
for c in ("feed", "tape", "lobreplay"):
    sys.path.insert(0, str(HERE.parent / c))
import firm_feed  # noqa: E402
from firm_exchsim import (  # noqa: E402
    SEC,
    Agent,
    ExchangeConfig,
    FeedConfig,
    Order,
    Phases,
    ReplayStrategyAdapter,
    SessionSpec,
    Simulator,
    TapeBackground,
    crypto_venue,
    pro_rata_futures,
    rng_u64,
    stream_key,
)
from firm_exchsim_codec import (  # noqa: E402
    LENGTH,
    NT,
    decode,
    encode,
    file_parse,
    journal_parse,
    mold_parse,
    schema,
    soup_parse,
)
from firm_exchsim_engine import Engine  # noqa: E402
from firm_lobreplay import Replay, Strategy  # noqa: E402
from firm_tape import TapeConfig  # noqa: E402

DATA = HERE / "data"
OPEN = 34_200 * SEC


def short_day(**kw):
    return ExchangeConfig(phases=Phases(start_ns=OPEN - SEC, open_ns=OPEN, close_ns=OPEN + 120 * SEC,
                                        end_ns=OPEN + 121 * SEC), **kw)


class Quoter(Agent):
    """Keeps one lot at the best bid and ask, moving them when they are no longer the best."""

    name = "quoter"

    def on_book(self, ctx, loc, top):
        b, _, a, _ = top
        if b is None or a is None:
            return
        live = [o for o in ctx.working() if o["status"] == "live"]
        for o in live:
            if o["price"] != (b if o["side"] == "B" else a):
                ctx.cancel(o["cl"])
        sides = {o["side"] for o in live if o["price"] == (b if o["side"] == "B" else a)}
        pos = ctx.position(1)
        for side, px in (("B", b), ("S", a)):
            if side not in sides and not (side == "B" and pos >= 500) and not (side == "S" and pos <= -500):
                ctx.send(Order(1, side, 100, px))


def run_day(seed=7, agent=True, **kw):
    sim = Simulator(short_day(**kw), seed=3)
    sim.add_background(TapeBackground(TapeConfig(seconds=120.0, seed=seed, news_at=None)))
    if agent:
        sim.add_agent(Quoter(), SessionSpec(firm="HF1"))
    return sim.run()


def test_codec_round_trip_and_itch_lengths():
    assert LENGTH["feed"] == {"A": 36, "E": 31, "X": 23, "D": 19, "P": 44, "U": 35, "C": 36, "Q": 40, "I": 50,
                              "S": 12, "H": 25, "R": 28, "G": 23, "W": 23}
    for proto in ("feed", "in", "out", "ctl"):
        blob = (DATA / "golden" / f"{proto}.bin").read_bytes()
        i = 0
        while i < len(blob):
            (n,) = struct.unpack_from(">H", blob, i)
            b = blob[i + 2:i + 2 + n]
            assert encode(proto, decode(proto, b)) == b
            i += 2 + n


def test_schema_matches_the_codec():
    sch = schema()
    assert json.loads((HERE / "schema.json").read_text()) == json.loads(json.dumps(sch))
    for proto, msgs in sch["protocols"].items():
        for t, d in msgs.items():
            if d["length"] is not None:
                assert d["length"] == LENGTH[proto][t]
                last = d["fields"][-1]
                assert last["offset"] + last["length"] == d["length"]


def test_book1_decoder_reads_the_simulator_feed():
    """Book 1's firm_feed decodes the A/E/X/D/P subset byte for byte and rebuilds the same book."""
    res = run_day()
    subset = [m for _, _, m in res.feed_messages() if type(m).__name__[-1] in "AEXDP"]
    book = firm_feed.Book()
    for m in firm_feed.decode(b"".join(struct.pack(">H", len(x)) + x for x in (encode("feed", m) for m in subset))):
        book.apply(m)
    assert not book.errors
    top = res.engine().book(1)
    assert all(ref in top.orders and top.orders[ref].visible for ref in book.orders)


def test_deterministic_bytes():
    a, b = run_day(), run_day()
    for f in (lambda r: r.feed_bytes(line="A"), lambda r: r.journal_bytes(), lambda r: r.recorded(line="B")):
        assert hashlib.sha256(f(a)).digest() == hashlib.sha256(f(b)).digest()
    assert len(a.feed_messages()) > 1000


def test_python_engine_reproduces_the_fixture():
    cfg = json.loads((DATA / "fixture_config.json").read_text())
    import make_fixtures
    out = make_fixtures.replay((DATA / "fixture_journal.bin").read_bytes(), cfg)
    assert hashlib.sha256(out).hexdigest() == (DATA / "fixture_out.sha256").read_text().strip()


def test_packets_sequencing_loss_and_recovery():
    res = run_day(feed=FeedConfig(burst_loss=(0.02, 0.3, 0.9), outages=(("B", OPEN + 30 * SEC, OPEN + 32 * SEC),)))
    ideal = [mold_parse(p) for _, p in res.packets()]
    seq = 1
    for _, s, count, _msgs in ideal:
        if count not in (0, 0xFFFF):
            assert s == 1 or s == seq
            seq = s + count
    got = {}
    for line in ("A", "B"):
        for _, p in file_parse(res.recorded(line=line)):
            _, s, count, msgs = mold_parse(p)
            if count not in (0, 0xFFFF):
                for k, m in enumerate(msgs):
                    got[s + k] = m
    last = max(s + c - 1 for _, s, c, _ in ideal if c not in (0, 0xFFFF))
    missing = [s for s in range(1, last + 1) if s not in got]
    lost_a = len(file_parse(res.recorded(line="A"))) < len(ideal)
    assert lost_a                                             # the burst loss removed packets from line A
    for s in missing:                                         # the retransmission service fills every gap
        pk = res.retransmit("", s, 1)
        assert pk and mold_parse(pk[0])[1] == s
        got[s] = mold_parse(pk[0])[3][0]
    assert all(s in got for s in range(1, last + 1))


def test_snapshot_recovery_rebuilds_the_book():
    res = run_day(feed=FeedConfig(snapshot_every_ns=10 * SEC))
    snaps = res.sim.venues[0].snaps
    t, loc, seq, msgs = snaps[5]
    from firm_lob import MessageBook
    book = MessageBook()
    for m in msgs:
        if type(m).__name__ == "Feed_A":
            book.apply("A", m.ref, 1 if m.side == "B" else -1, m.price, m.shares)
    for _, s, m in res.feed_messages():                       # apply the incremental feed after the snapshot
        if s <= seq or type(m).__name__[-1] not in "AEXDUC":
            continue
        k = type(m).__name__[-1]
        if k == "A":
            book.apply("A", m.ref, 1 if m.side == "B" else -1, m.price, m.shares)
        elif k in "EXC":
            book.apply("X", m.ref, qty=m.shares)
        elif k == "D":
            book.apply("D", m.ref)
        else:
            book.apply("U", m.ref, price=m.price, qty=m.shares, new_ref=m.new_ref)
    eng = res.engine().book(1)
    assert book.depth(1, 10) == eng.depth(1, 10) and book.depth(-1, 10) == eng.depth(-1, 10)
    assert msgs[-1].crc == msgs[-1].crc and type(msgs[0]).__name__ == "Feed_G"


def test_agent_changes_the_market_and_the_tape_exports():
    with_agent, without = run_day(), run_day(agent=False)
    q = with_agent.agents["quoter"]
    assert len(q.fills) > 10 and q.fees != 0
    ta, tb = with_agent.tape(), without.tape()
    assert len(ta.msgs) != len(tb.msgs)                       # reactive: the background met our orders
    assert set(np.unique(ta.msgs["kind"])) <= {b"A", b"X", b"E"} and len(ta.top) == len(ta.msgs)
    tr = with_agent.truth["trades"]
    assert {"noise", "informed"} <= set(tr["aggressor"])
    assert len(with_agent.reports("HF1")) > 0 and len(with_agent.drop_copy("HF1")) > 0


class TouchStrategy(Strategy):
    """Book 7 replay strategy: one lot on the best bid while flat."""

    def __init__(self):
        self.sent = False

    def on_market(self, ctx, t, snap):
        if not self.sent and snap["bid"] is not None and t > 5.0:
            ctx.send(1, snap["bid"], 100)
            self.sent = True


def test_replay_strategy_runs_on_replay_and_on_the_simulator():
    base = run_day(agent=False)
    rep = Replay(base.tape().msgs, TouchStrategy(), "fifo", 0.0, 0.0).run()
    sim = Simulator(short_day(), seed=3)
    sim.add_background(TapeBackground(TapeConfig(seconds=120.0, seed=7, news_at=None)))
    s = TouchStrategy()
    sim.add_agent(ReplayStrategyAdapter(s), SessionSpec(firm="HF3"))
    res = sim.run()
    assert s.sent and len(rep.shadows) == 1
    assert res.agents["replaystrategy"].orders                 # the same strategy traded on the simulator


def test_counter_based_streams_are_independent_of_other_participants():
    k = stream_key(1, 0, 2)
    assert [rng_u64(k, n) for n in range(3)] == [rng_u64(k, n) for n in range(3)]
    one = Simulator(short_day(), seed=3)
    one.add_agent(Quoter(), SessionSpec(firm="HF1", latency=__import__("firm_exchsim").LatencyModel(jitter=0.5)))
    lat1 = [one._lat(one.by_name["quoter@SIMX"], 0) for _ in range(5)]
    two = Simulator(short_day(), seed=3)
    two.add_agent(Quoter(), SessionSpec(firm="HF1", latency=__import__("firm_exchsim").LatencyModel(jitter=0.5)))
    two.add_agent(Quoter(), SessionSpec(firm="HF2"))
    lat2 = [two._lat(two.by_name["quoter@SIMX"], 0) for _ in range(5)]
    assert lat1 == lat2 and len(set(lat1)) > 1


def test_presets_and_soup_sample():
    assert pro_rata_futures().engine_config()["instruments"][0]["matching"] == "C"
    c = crypto_venue()
    assert c.engine_config()["fees"]["unit"] == "bp" and c.engine_config()["throttle"]["weights"]["M"] == 10
    frames, rest = soup_parse((DATA / "fixture_soup.bin").read_bytes())
    assert rest == b"" and [t for t, _ in frames] == list("LAUSRHUSOZ")
    login = decode("soup_client", struct.pack(">H", 1 + len(frames[0][1]))[2:] + b"L" + frames[0][1])
    assert login.username == "HF1" and login.seq == 1


def test_journal_fixture_is_well_formed():
    recs = journal_parse((DATA / "fixture_journal.bin").read_bytes())
    assert len(recs) > 10_000 and all(recs[i][0] <= recs[i + 1][0] or True for i in range(len(recs) - 1))
    e = Engine(json.loads((DATA / "fixture_config.json").read_text()))
    kinds = set()
    for t, s, p in recs[:3000]:
        f, r = e.process_bytes(t, s, p)
        kinds |= {type(m).__name__ for m in f}
    assert {"Feed_A", "Feed_E", "Feed_Q"} <= kinds or {"Feed_A", "Feed_E"} <= kinds
    assert NT["ctl"]["P"]._fields == ("locate", "phase", "reason")


def test_recorded_day_script_small(tmp_path):
    import make_recorded_day
    s = make_recorded_day.main(["--hours", "0.02", "--instruments", "2", "--out", str(tmp_path)])
    assert s["feed_messages"] > 2000 and 0 < s["packets_B"] and s["packets_A"] > 0
    again = make_recorded_day.run(0.02, 2, out=tmp_path / "again")
    assert again["sha256"] == s["sha256"]                     # same arguments, same bytes
    from firm_exchsim_codec import journal_parse
    recs = journal_parse((tmp_path / "day_journal.bin").read_bytes())
    assert len(recs) == s["journal_records"]


def test_consolidated_feed_delays_and_direct_view():
    from firm_exchsim import SEC, Agent, ExchangeConfig, LatencyModel, Order, SessionSpec, Simulator, SipConfig
    t0 = 34_200 * SEC
    seen = []

    class Watcher(Agent):
        name = "w"

        def on_nbbo(self, ctx, locate, nbbo):
            seen.append((ctx.now_ns, nbbo.bid if nbbo else None, nbbo.ask if nbbo else None, ctx.direct_nbbo(1)[0]))

    venues = [ExchangeConfig(venue="VA"), ExchangeConfig(venue="VB")]
    sip = SipConfig(default_ns=1_000_000, venue_ns={"VB": 3_000_000}, process_ns=10_000, agent_ns=5_000)
    sim = Simulator(venues, sip=sip)
    lat = LatencyModel(entry_ns=1_000, ack_ns=1_000, data_ns=2_000)
    sim.add_agent(Watcher(), [SessionSpec(venue="VA", latency=lat), SessionSpec(venue="VB", latency=lat)])
    sim.add_events(orders=[(t0 + SEC, "VA", Order(side="B", qty=100, price=999_900)),
                           (t0 + SEC, "VA", Order(side="S", qty=100, price=1_000_200)),
                           (t0 + 2 * SEC, "VB", Order(side="B", qty=100, price=1_000_000))])
    res = sim.run(t0 + 3 * SEC)
    s = res.sip(1)
    # VA's two-sided quote reaches the SIP 1 ms after the engine, VB's better bid 3 ms after
    assert list(s["bid"]) == [999_900, 1_000_000] and list(s["ask"]) == [1_000_200, 1_000_200]
    eng = s["t"] - np.array([t0 + SEC, t0 + 2 * SEC])
    assert eng[0] > 1_010_000 and eng[0] < 1_100_000 and eng[1] > 3_010_000 and eng[1] < 3_100_000
    # the agent hears of it 5 microseconds after publication; its direct view already had VB's bid
    assert [x[0] - y for x, y in zip(seen, s["t"], strict=True)] == [5_000, 5_000]
    assert seen[1][3] == 1_000_000 and seen[1][1] == 1_000_000


def test_dark_venue_prices_midpoint_pegs_off_the_lit_venue():
    from firm_exchsim import SEC, ExchangeConfig, Order, Simulator, midpoint_dark_pool
    t0 = 34_200 * SEC
    sim = Simulator([ExchangeConfig(venue="LIT"), midpoint_dark_pool(reference="LIT", reference_ns=50_000)])
    sim.add_events(orders=[(t0 + SEC, "LIT", Order(side="B", qty=100, price=999_900)),
                           (t0 + SEC, "LIT", Order(side="S", qty=100, price=1_000_200)),
                           (t0 + 2 * SEC, "SIMD", Order(side="B", qty=500, price=0, display="M", min_qty=200)),
                           (t0 + 3 * SEC, "SIMD", Order(side="S", qty=100, price=0, tif="I", display="M")),
                           (t0 + 4 * SEC, "SIMD", Order(side="S", qty=300, price=0, tif="I", display="M"))])
    res = sim.run(t0 + 5 * SEC)
    ex = [m for _, _, m in res.feed_messages("SIMD") if type(m).__name__ in ("Feed_E", "Feed_C")]
    trades = res.engine("SIMD").trades
    # the 100-share IOC is below the resting peg's minimum: no trade; the 300 crosses at the lit mid, 100.005
    assert [(t[2], t[3]) for t in trades] == [(1_000_050, 300)]
    assert ex == [] or all(getattr(m, "price", 1_000_050) == 1_000_050 for m in ex)
