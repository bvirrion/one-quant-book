"""System design: the numbers in each answer, and small models of each design's key property.

A model is not the system: nothing here runs on a network or a real exchange. Each model meets a slow independent check, a
random stream or a broken twin. Six answers are prose, listed in NONNUMERIC. The ledger holds what a run cannot show.
"""
import collections
import itertools
import math
import pathlib
import random
import statistics
import subprocess
import sys
import threading
import zlib

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
PY = HERE / "python"
sys.path.insert(0, str(PY))

import iv_bitemporal  # noqa: E402
import iv_book_sync  # noqa: E402
import iv_budget  # noqa: E402
import iv_bulkhead  # noqa: E402
import iv_checkpoint  # noqa: E402
import iv_conflate  # noqa: E402
import iv_consumer  # noqa: E402
import iv_delta  # noqa: E402
import iv_exchange  # noqa: E402
import iv_group_commit  # noqa: E402
import iv_journal  # noqa: E402
import iv_ledger  # noqa: E402
import iv_order_states  # noqa: E402
import iv_queue  # noqa: E402
import iv_quorum  # noqa: E402
import iv_recon  # noqa: E402
import iv_ring  # noqa: E402
import iv_risk  # noqa: E402
import iv_route  # noqa: E402
import iv_run_key  # noqa: E402
import iv_session  # noqa: E402

NONNUMERIC = {
    6: "A judgement on what belongs on the hot path; no number decides it",
    12: "A design of a stop control; its facts rest on the rule and the order in the ledger",
    17: "Reasoning about clocks and paths, with nothing to compute",
    28: "A list of causes and the design that removes them",
    31: "An argument for one thread and for partitioning, with the arithmetic in the text; see test_q38 for the model",
    37: "A release procedure; its facts rest on the order in the ledger",
}


def py(script):
    r = subprocess.run([sys.executable, str(PY / f"{script}.py")], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return r.stdout.splitlines()


def test_q1():
    rate, service, rng = 50_000.0, 15e-6, random.Random(1)  # a stable single server; the law needs no more
    t = wait = area = 0.0
    n = 200_000
    for _ in range(n):                         # Little's law on a simulated queue: time in system over total time
        area += wait + service
        gap = rng.expovariate(rate)
        t += gap
        wait = max(0.0, wait + service - gap)
    w = area / n
    assert area / t == pytest.approx(rate * w, rel=0.02)
    assert rate * 40e-6 == pytest.approx(2.0) and 200 / rate == pytest.approx(0.004)


def test_q2():
    def slow(n):
        return 1 - 0.99**n

    assert slow(10) == pytest.approx(0.0956, abs=1e-4) and slow(100) == pytest.approx(0.634, abs=1e-3)
    rng = random.Random(2)
    hits = sum(any(rng.random() < 0.01 for _ in range(10)) for _ in range(100_000))
    assert hits / 100_000 == pytest.approx(slow(10), abs=0.004)
    assert slow(0) == 0 and slow(1) == pytest.approx(0.01)


def test_q3():
    assert 1_000_000 * 40 * 8 == 320_000_000
    day = 200_000 * 40 * 6.5 * 3600
    assert day == pytest.approx(187.2e9) and day * 252 == pytest.approx(47.17e12, rel=1e-3)


def test_q4():
    hours = 365 * 24
    assert (1 - 0.999) * hours == pytest.approx(8.76)
    assert (1 - 0.999**2) * hours == pytest.approx(17.5, abs=0.02)
    assert (0.001**2) * hours * 3600 == pytest.approx(31.5, abs=0.1)
    rng = random.Random(4)
    up = [(rng.random() >= 0.001, rng.random() >= 0.001) for _ in range(1_000_000)]
    assert sum(a and b for a, b in up) / 1e6 == pytest.approx(0.998, abs=2e-4)
    assert sum(a or b for a, b in up) / 1e6 >= 0.99999


def test_q5():
    assert py("retry") == ["2 [100, 100]", "1 [100]"]


def test_q7():
    rng = random.Random(7)
    seen = []
    for _ in range(100_000):                   # a change at a random moment waits for the next poll
        seen.append(1.0 - rng.random())
    assert statistics.mean(seen) == pytest.approx(0.5, abs=0.01) and max(seen) <= 1.0
    assert 10_000 / 1 == 10_000 and 10_000 * 2 == 20_000 and round(10_000 / 60) == 167

    def server_sends(seconds, changes_per_second):
        """Counts what the server sends in a run: one reply per poll, or one message per change per client."""
        replies = sum(10_000 for _ in range(seconds))
        pushes = sum(10_000 for _ in range(int(seconds * changes_per_second)))
        return replies / seconds, pushes / seconds

    assert server_sends(600, 2) == (10_000, 20_000)
    assert server_sends(600, 1 / 60)[0] == 10_000 and server_sends(600, 1 / 60)[1] == pytest.approx(166.67, abs=0.01)


def test_q8():
    assert 1 / 2e-6 == pytest.approx(500_000)
    assert iv_queue.mean_time_in_system(0.8, service=2.0, n=300_000) == pytest.approx(2 / 0.2, rel=0.1)
    # at the extreme: past capacity the queue never settles, so a longer run gives a longer wait
    short = iv_queue.mean_time_in_system(1.1, n=5_000)
    long = iv_queue.mean_time_in_system(1.1, n=50_000)
    assert long > 5 * short


def test_q9():
    keys = [f"k{i}" for i in range(40_000)]
    ten, eleven = iv_ring.Ring([f"n{i}" for i in range(10)]), iv_ring.Ring([f"n{i}" for i in range(11)])
    moved = [k for k in keys if ten.node(k) != eleven.node(k)]
    assert 0.07 < len(moved) / len(keys) < 0.12
    assert all(eleven.node(k) == "n10" for k in moved)           # a key moves only onto the new node
    plain = sum(iv_ring.modulo_node(k, 10) != iv_ring.modulo_node(k, 11) for k in keys) / len(keys)
    assert plain == pytest.approx(10 / 11, abs=0.01)

    def worst(vnodes):
        ring = iv_ring.Ring([f"n{i}" for i in range(10)], vnodes)
        return max(collections.Counter(ring.node(k) for k in keys).values()) / (len(keys) / 10)

    assert worst(1) > 1.5 and worst(100) < 1.25 and worst(1000) < worst(100)


def test_q10():
    S = iv_order_states
    o = S.Order(100)
    for event, n, state in [("ack", 0, S.OPEN), ("fill", 40, S.OPEN), ("cancel_req", 0, S.PENDING_CANCEL),
                            ("fill", 60, S.FILLED), ("cancel_rej", 0, S.FILLED)]:
        assert o.on(event, n) == state        # the cancel crossed the last fill
    a = S.Order(100)
    a.on("ack")
    assert a.on("cancel_ack") == S.CANCELLED  # the venue cancelled it unasked
    with pytest.raises(ValueError):
        a.on("fill", 1)
    with pytest.raises(ValueError):
        S.Order(10).on("fill", 1)
    b = S.Order(10)
    b.on("ack")
    with pytest.raises(ValueError):
        b.on("fill", 11)
    assert S.Order(10).on("reject") == S.REJECTED
    rng = random.Random(10)
    events = ["ack", "reject", "fill", "cancel_req", "cancel_ack", "cancel_rej"]
    for _ in range(3000):                      # whatever arrives: a final state stays final, and never an overfill
        o = S.Order(rng.randint(1, 20))
        final = None
        for _ in range(rng.randint(1, 12)):
            try:
                state = o.on(rng.choice(events), rng.randint(1, 5))
            except ValueError:
                continue
            assert final is None or state == final
            if state in S.FINAL:
                final = state
            assert o.filled <= o.qty and (o.state != S.FILLED or o.filled == o.qty)


def test_q11():
    rng = random.Random(11)
    for _ in range(300):
        r = iv_risk.Risk(limit=1000, max_qty=300, collar=0.05)
        working = []
        for _ in range(200):
            roll = rng.random()
            if roll < 0.5:
                side, qty = rng.choice(["buy", "sell"]), rng.randint(1, 350)
                if r.allow(side, qty, 100.0, 100.0) == "ok":
                    working.append([side, qty])
            elif working:
                order = rng.choice(working)
                working.remove(order)
                done = rng.randint(0, order[1])
                r.on_fill(order[0], done)
                r.on_cancel(order[0], order[1] - done)
            # the claim itself: if every open order filled now, the position would still be inside the limit
            assert r.position + r.open_buys <= 1000 and r.position - r.open_sells >= -1000
    q = iv_risk.Risk(1000, 300, 0.05)
    assert q.allow("buy", 301, 100.0, 100.0) == "size"
    assert q.allow("buy", 10, 106.0, 100.0) == "collar"
    assert q.allow("buy", 10, 105.0, 100.0) == "ok"
    for _ in range(33):
        q.allow("buy", 30, 100.0, 100.0)
    assert q.open_buys == 1000 and q.allow("buy", 1, 100.0, 100.0) == "position"
    assert q.position == 0                     # a check on position alone would have let these through
    assert q.allow("sell", 300, 100.0, 100.0) == "ok"   # a sell does not add to the long side, and is inside the short limit


def test_q13():
    rng = random.Random(13)
    for _ in range(300):
        truth = {0: {}}
        book = {}
        stream = []
        for seq in range(1, 300):
            price, qty = rng.randint(1, 8), rng.choice([0, 1, 2, 3])
            if qty:
                book[price] = qty
            else:
                book.pop(price, None)
            truth[seq] = dict(book)
            stream.append((seq, price, qty))
        sync = iv_book_sync.BookSync()
        loss = rng.choice([0.0, 0.01, 0.05])
        for seq, price, qty in stream:
            if rng.random() >= loss:
                sync.on_incremental(seq, price, qty)
            if rng.random() < 0.02:            # a snapshot of a moment a little in the past
                at = max(0, seq - rng.randint(0, 5))
                sync.on_snapshot(at, truth[at])
            if sync.book is not None:
                assert sync.book == truth[sync.last]     # never a book that is wrong for its sequence
    s = iv_book_sync.BookSync()
    s.on_incremental(5, 1, 1)
    s.on_snapshot(2, {})                       # the snapshot is older than the buffer: 3 and 4 are gone
    assert s.book is None
    s.on_snapshot(5, {1: 1})
    assert s.book == {1: 1} and s.last == 5
    s.on_incremental(7, 1, 2)                  # a gap once in sync drops the book
    assert s.book is None and s.buffer == [(7, 1, 2)]


def test_q14():
    rng = random.Random(14)
    for _ in range(200):
        c = iv_conflate.Conflator()
        newest = {}
        delivered = {}
        firsts = []
        for _ in range(500):
            if rng.random() < 0.8:
                sym, value = rng.randint(0, 9), rng.random()
                c.put(sym, value)
                newest[sym] = value
                if sym not in firsts:
                    firsts.append(sym)
            else:
                n = rng.randint(0, 3)
                got = c.take(n)
                assert [s for s, _ in got] == firsts[:len(got)]   # a busy symbol cannot keep others waiting
                firsts = firsts[len(got):]
                delivered.update(got)
            assert len(c.latest) <= 10
        delivered.update(c.take(100))
        assert delivered == newest             # the consumer ends with the newest value of everything
    assert iv_conflate.Conflator().take(5) == []


def test_q15():
    backlog, t = 0.0, 0.0
    while backlog < 16 * 2**20:                # net of what the client reads, a millisecond at a time
        backlog += (10_000 - 5_000) * 100 * 0.001
        t += 0.001
    assert t == pytest.approx(33.55, abs=0.01)
    assert 16 * 2**20 / ((10_000 - 5_000) * 100) == pytest.approx(33.55, abs=0.01)


def test_q16():
    assert 1_000_000 * 100 * 50 * 8 == 40e9
    assert 1_000_000 * 10 * 50 * 8 == 4e9
    assert 1_000_000 / 20_000 == 50 and 40e9 / 50 == 800e6


def test_q18():
    ratio, flags = py("iv_columns")
    assert float(ratio) < 0.5 and flags == "True True"


def test_q19():
    ts = list(range(1_700_000_000_000_000_000, 1_700_000_000_000_000_000 + 10_000_000, 1000))
    data = iv_delta.encode(ts)
    assert iv_delta.decode(data) == ts and len(data) == 20007
    rng = random.Random(19)
    for _ in range(200):
        values = [rng.randint(-(2**62), 2**62) for _ in range(rng.randint(0, 40))]
        assert iv_delta.decode(iv_delta.encode(values)) == values
    wild = [rng.getrandbits(62) for _ in range(1000)]
    assert len(iv_delta.encode(wild)) > 8 * len(wild)   # at the extreme, unsorted random data grows
    assert iv_delta.encode([]) == b""


def test_q20():
    rng = random.Random(20)
    for _ in range(300):
        table = iv_bitemporal.Bitemporal()
        rows = sorted(((rng.randint(0, 5), k, rng.random()) for k in range(rng.randint(0, 30))), key=lambda r: r[1])
        for event, known, value in rows:
            table.insert(event, known, value)
        for at in range(-1, 32):
            state = {}                         # the slow way: replay every correction up to that time
            for event, known, value in rows:
                if known <= at:
                    state[event] = value
            assert table.as_of(at) == dict(sorted(state.items()))
    t = iv_bitemporal.Bitemporal()
    t.insert(1, 10, "first")
    t.insert(1, 20, "corrected")
    assert t.as_of(15) == {1: "first"} and t.as_of(25) == {1: "corrected"} and t.as_of(5) == {}


def test_q21():
    venues = {"A": (0.003, [(10.00, 100), (10.01, 200)]), "B": (0.001, [(10.00, 150), (10.02, 300)]),
              "C": (-0.002, [(10.01, 100), (10.03, 500)])}
    plan, cost = iv_route.route(venues, 300)
    assert plan == {"B": 150, "A": 100, "C": 50} and cost == pytest.approx(3000.85)
    with pytest.raises(ValueError):
        iv_route.route(venues, 10_000)
    rng = random.Random(21)

    def walk(levels, fee, k):
        total = 0.0
        for price, size in sorted(levels):
            take = min(k, size)
            total += take * (price + fee)
            k -= take
        return total

    for _ in range(100):                       # against every possible split across three venues
        v = {n: (rng.choice([-1, 0, 1, 2]) / 1000, [(10 + rng.randint(0, 4) / 100, rng.randint(1, 6)) for _ in range(2)])
             for n in "ABC"}
        room = {n: sum(s for _, s in v[n][1]) for n in v}
        qty = rng.randint(1, sum(room.values()))
        best = min(walk(v["A"][1], v["A"][0], a) + walk(v["B"][1], v["B"][0], b) + walk(v["C"][1], v["C"][0], qty - a - b)
                   for a in range(room["A"] + 1) for b in range(room["B"] + 1) if 0 <= qty - a - b <= room["C"])
        assert iv_route.route(v, qty)[1] == pytest.approx(best)


def test_q22():
    rng = random.Random(22)
    for _ in range(300):
        theirs = {f"e{i}": (f"o{i % 7}", rng.randint(1, 9), 100 + i) for i in range(rng.randint(0, 40))}
        ours = dict(theirs)
        keys = list(theirs)
        rng.shuffle(keys)
        lost, changed = keys[:3], keys[3:6]
        for k in lost:
            del ours[k]
        for k in changed:
            ours[k] = (ours[k][0], ours[k][1] + 1, ours[k][2])
        ours["ghost"] = ("o", 1, 1)
        r = iv_recon.reconcile(ours, theirs)
        assert r == {"missing": sorted(lost), "extra": ["ghost"], "differ": sorted(changed)}
    assert iv_recon.reconcile({}, {}) == {"missing": [], "extra": [], "differ": []}


def test_q23(tmp_path):
    path = str(tmp_path / "ledger.db")
    db = iv_ledger.connect(path)
    db.execute("INSERT INTO entries VALUES ('seed', 'A', 100)")
    assert iv_ledger.transfer(db, "r1", "A", "B", 30) == "ok"
    assert iv_ledger.transfer(db, "r1", "A", "B", 30) == "ok"            # a retry changes nothing
    assert iv_ledger.balance(db, "A") == 70 and iv_ledger.balance(db, "B") == 30
    with pytest.raises(RuntimeError):
        iv_ledger.transfer(db, "r2", "A", "B", 10, fail_after_first=True)
    assert iv_ledger.balance(db, "A") == 70                               # the half-done transfer left nothing
    assert iv_ledger.transfer(db, "r3", "A", "B", 1000) == "insufficient"
    assert iv_ledger.transfer(db, "r3", "A", "B", 1) == "insufficient"    # the first answer stands
    for bad in (-50, 0):                       # a negative amount would pass the check and overdraw the target
        with pytest.raises(ValueError):
            iv_ledger.transfer(db, f"neg{bad}", "A", "B", bad)
    assert iv_ledger.balance(db, "A") == 70 and iv_ledger.balance(db, "B") == 30
    assert db.execute("SELECT count(*) FROM done WHERE request LIKE 'neg%'").fetchone()[0] == 0
    assert iv_ledger.transfer(db, "r4", "B", "A", 30) == "ok" and iv_ledger.balance(db, "B") == 0
    assert iv_ledger.transfer(db, "r5", "A", "B", 30) == "ok" and iv_ledger.balance(db, "B") == 30
    results = []

    def worker(k):
        conn = iv_ledger.connect(path)
        results.append(iv_ledger.transfer(conn, f"t{k}", "A", "B", 30))
        conn.close()

    threads = [threading.Thread(target=worker, args=(k,)) for k in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results.count("ok") == 2 and iv_ledger.balance(db, "A") == 10  # no overdraft under concurrent transfers
    total = db.execute("SELECT sum(amount) FROM entries WHERE request != 'seed'").fetchone()[0]
    assert total == 0                          # every transfer's rows add to zero


def test_q24():
    stage = [(10, 0.98), (100, 0.02)]
    d = iv_budget.distribution_of_sum([stage] * 3)
    assert iv_budget.percentile({10: 0.98, 100: 0.02}, 0.99) == 100
    assert iv_budget.percentile(d, 0.99) == 120 and iv_budget.percentile(d, 0.5) == 30
    assert sum(v * p for v, p in d.items()) == pytest.approx(35.4) and sum(d.values()) == pytest.approx(1.0)
    rng = random.Random(24)
    sums = sorted(sum(100 if rng.random() < 0.02 else 10 for _ in range(3)) for _ in range(200_000))
    assert sums[int(0.99 * len(sums))] == 120
    together = sorted(300 if rng.random() < 0.02 else 30 for _ in range(100_000))   # if all stages are slow at once
    assert together[int(0.99 * len(together))] == 300


def test_q25():
    for rho, target in [(0.5, 2.0), (0.9, 10.0)]:
        assert iv_queue.mean_time_in_system(rho) == pytest.approx(target, rel=0.1)
    assert iv_queue.mean_time_in_system(0.5, fixed_service=True) == pytest.approx(1.5, rel=0.05)
    assert iv_queue.mean_time_in_system(0.9, fixed_service=True) == pytest.approx(5.5, rel=0.1)
    assert iv_queue.mean_time_in_system(0.99) > 50       # slow to converge; see the answer
    assert iv_queue.mean_time_in_system(0.01) == pytest.approx(1.0, rel=0.05)


def test_q26():
    latency, batch, _ = iv_group_commit.simulate(10_000, 0.002)
    assert latency == pytest.approx(0.003, rel=0.05) and batch == pytest.approx(20, rel=0.05)
    light, one, _ = iv_group_commit.simulate(300, 0.002, n=1000)
    assert light == pytest.approx(0.002, rel=0.01) and one == 1.0        # at low load nothing waits to batch
    behind = iv_group_commit.simulate(10_000, 0.002, n=1000, group=False)
    longer = iv_group_commit.simulate(10_000, 0.002, n=2000, group=False)
    assert behind[0] > 0.5 and longer[0] > 1.8 * behind[0]               # one flush each falls further behind


def test_q27():
    key = iv_run_key.run_key
    base = key("abc", "v7", {"lookback": 20, "cost": 0.5})
    assert base == key("abc", "v7", {"cost": 0.5, "lookback": 20})       # dict order does not matter
    assert base != key("abd", "v7", {"lookback": 20, "cost": 0.5})
    assert base != key("abc", "v8", {"lookback": 20, "cost": 0.5})
    assert base != key("abc", "v7", {"lookback": 21, "cost": 0.5})
    with pytest.raises(ValueError):
        key("abc", "latest", {})


def test_q29():
    orders = [(float(i), "A" if i % 2 == 0 else "B") for i in range(20)]
    service = {"A": 0.01, "B": 50.0}
    shared, split = iv_bulkhead.simulate(orders, service, True), iv_bulkhead.simulate(orders, service, False)
    assert shared["A"] == pytest.approx(433.09) and split["A"] == pytest.approx(0.01)
    # by hand: the last healthy order, at 18 s, waits for 9 stalled orders and 9 healthy ones, from the first stall at 1 s
    assert 1 + 9 * 50.0 + 9 * 0.01 - 18 == pytest.approx(shared["A"])
    longer = [(float(i), "A" if i % 2 == 0 else "B") for i in range(40)]
    assert iv_bulkhead.simulate(longer, service, True)["A"] > 2 * shared["A"]   # it keeps growing with the run
    assert iv_bulkhead.simulate(longer, service, False)["A"] == pytest.approx(0.01)
    alone = iv_bulkhead.simulate([o for o in orders if o[1] == "A"], service, True)
    assert split["A"] == pytest.approx(alone["A"])       # the healthy venue behaves as if the other did not exist
    fair = iv_bulkhead.simulate(orders, {"A": 0.01, "B": 0.01}, True)
    assert fair["A"] == pytest.approx(0.01)              # at the extreme of no stall, sharing costs nothing here


def test_q30(tmp_path):
    bodies = [bytes([k]) * (k * 3) for k in range(40)]
    path = tmp_path / "j"
    with open(path, "wb") as f:
        for b in bodies:
            iv_journal.append(f, b)
    data = path.read_bytes()
    assert iv_journal.recover(data) == (bodies, len(data))
    ends = list(itertools.accumulate(8 + len(b) for b in bodies))
    for cut in range(len(data) + 1):           # a crash can tear the file at any byte
        records, at = iv_journal.recover(data[:cut])
        whole = sum(e <= cut for e in ends)
        assert records == bodies[:whole] and at == (ends[whole - 1] if whole else 0)
    rng = random.Random(30)
    for _ in range(300):
        i = rng.randrange(len(data))           # a flipped bit stops recovery at that record, and never passes it
        bad = bytearray(data)
        bad[i] ^= 1 << rng.randrange(8)
        records, _ = iv_journal.recover(bytes(bad))
        assert records == bodies[:len(records)] and len(records) <= sum(e <= i for e in ends)
    assert 5e9 / 1e6 / 60 == pytest.approx(83.3, abs=0.1)
    good = data[:ends[1]]
    for zeros in (1, 7, 8, 9, 16, 4096):       # a file grown over bytes never written: zeros are the commonest garbage
        assert iv_journal.recover(good + bytes(zeros)) == (bodies[:2], len(good))
    assert iv_journal.recover(bytes(16)) == ([], 0)
    assert zlib.crc32(b"") == 0 and zlib.crc32(b"", iv_journal.SEED) != 0      # the reason for the seed
    per_second = 5e9 / (6.5 * 3600)            # the replay after a 5-minute snapshot, at a session's even rate
    assert per_second == pytest.approx(213_675, abs=1)
    assert per_second * 300 == pytest.approx(64.1e6, abs=0.1e6) and per_second * 300 / 1e6 == pytest.approx(64.1, abs=0.1)
    assert 5e9 * 300 / (24 * 3600) == pytest.approx(17.4e6, abs=0.1e6)   # over 24 hours, less
    assert 1e6 * 300 == 300e6 and 1e6 * 300 / 1e6 / 60 == 5.0   # events arriving as fast as the replay runs


def test_q32():
    rng = random.Random(32)
    high = low = False
    for _ in range(2000):
        log = [rng.randint(1, 9) for _ in range(rng.randint(1, 12))]
        crashes = [rng.randint(1, 40) for _ in range(rng.randint(0, 8))]
        assert iv_consumer.consume(log, "atomic", crashes) == sum(log)
        first = iv_consumer.consume(log, "apply_first", crashes)
        last = iv_consumer.consume(log, "commit_first", crashes)
        assert first >= sum(log) and last <= sum(log)
        high |= first > sum(log)
        low |= last < sum(log)
    assert high and low                        # each wrong order really does go wrong


def test_q33():
    assert py("iv_fencing") == ["False 250", "True 90"]


def test_q34():
    assert iv_quorum.commit_ms([0, 1, 40], iv_quorum.majority(3)) == 1
    assert iv_quorum.commit_ms([0, 1, 40], 3) == 40
    assert iv_quorum.commit_ms([0, 40], 2) == 40         # the near replica has died
    for n in range(1, 8):
        need = iv_quorum.majority(n)
        assert n - need == (n - 1) // 2                  # failures tolerated
        for a, b in itertools.product(itertools.combinations(range(n), need), repeat=2):
            assert set(a) & set(b)                       # any two majorities share a member


def test_q35():
    c, m = 60.0, 86400.0
    best = math.sqrt(2 * c * m)
    assert best == pytest.approx(3220, abs=1)

    def formula(t):
        return c / t + t / (2 * m)

    assert formula(best) == pytest.approx(0.0373, abs=2e-4)
    at_best = iv_checkpoint.overhead(best, c, m, work=1e8)
    assert at_best == pytest.approx(0.038, abs=0.0005) and at_best == pytest.approx(formula(best), rel=0.15)
    quarter, four = iv_checkpoint.overhead(best / 4, c, m, work=1e8), iv_checkpoint.overhead(best * 4, c, m, work=1e8)
    assert quarter == pytest.approx(0.08, abs=0.002) and four == pytest.approx(0.08, abs=0.004)
    assert quarter == pytest.approx(formula(best / 4), rel=0.15) and four == pytest.approx(formula(best * 4), rel=0.15)
    short = [iv_checkpoint.overhead(best, c, m, seed=s) for s in range(1, 9)]   # the default 2e6 s of work
    assert max(short) - min(short) > 0.01      # a short run is noisier: seeds differ by more than the point at issue
    assert iv_checkpoint.overhead(best, 0.0, 1e12, work=1e6) == pytest.approx(0.0, abs=1e-9)   # no failures, no cost


def test_q36():
    rng = random.Random(36)
    for _ in range(500):
        tx, rx = iv_session.Sender(max_age=5), iv_session.Receiver()
        now = 0
        lost_any = False
        sent_at = {}
        for k in range(rng.randint(1, 40)):
            now += rng.randint(0, 3)
            message = tx.send(now, rng.choice(["order", "status"]), k)
            sent_at[k] = now
            if rng.random() < 0.2:             # the connection drops: this one never arrives
                lost_any = True
                continue
            ask = rx.on_message(message)
            if ask is not None:
                accepted_before = len(rx.accepted)
                for m in tx.resend(ask, now):
                    assert rx.on_message(m) is None
                    if len(rx.accepted) > accepted_before and m[2] == "order":
                        assert now - sent_at[m[3]] <= 5    # no stale order is ever sent again
                    accepted_before = len(rx.accepted)
        final = rx.expected
        for m in tx.resend(final, now):
            assert rx.on_message(m) is None
        assert rx.expected == len(tx.sent) + 1           # every number is passed, none left open
        assert rx.accepted == sorted(rx.accepted) and len(set(rx.accepted)) == len(rx.accepted)
        assert lost_any or rx.accepted == list(range(len(tx.sent)))
    tx, rx = iv_session.Sender(max_age=5), iv_session.Receiver()
    old, young = tx.send(0, "order", "old"), tx.send(100, "order", "young")
    assert rx.on_message(young) == 1 and old[0] == 1
    for m in tx.resend(1, 101):
        rx.on_message(m)
    assert rx.accepted == ["young"] and rx.expected == 3
    rx.on_message(young)                       # a duplicate is ignored
    assert rx.accepted == ["young"]


def make_log(rng, n):
    return [(k, k * 1000, f"o{k}", rng.choice(["buy", "sell"]), rng.randint(95, 105), rng.randint(1, 50)) for k in range(n)]


def test_q38():
    rng = random.Random(38)
    for _ in range(100):
        log = make_log(rng, 200)
        primary = iv_exchange.Engine()
        for entry in log:
            primary.apply(*entry)
            if primary.bids and primary.asks:
                assert -primary.bids[0][0] < primary.asks[0][0]   # a book is never crossed
        traded = sum(e[6] for e in primary.events if e[0] == "trade") * 2
        resting = sum(o[3] for o in primary.bids + primary.asks)
        assert traded + resting == sum(e[5] for e in log)         # quantity is conserved
        k = rng.randrange(len(log))            # the primary dies after k entries; a standby replays and carries on
        standby = iv_exchange.Engine()
        for entry in log[:k]:
            standby.apply(*entry)
        for entry in log[k:]:
            standby.apply(*entry)
        assert standby.digest() == primary.digest()
    ticks = itertools.count()
    twin_a = iv_exchange.Engine(clock=lambda: next(ticks))
    twin_b = iv_exchange.Engine(clock=lambda: next(ticks))
    log = make_log(random.Random(1), 50)
    for entry in log:
        twin_a.apply(*entry)
    for entry in log:
        twin_b.apply(*entry)
    assert twin_a.digest() != twin_b.digest()  # read the time inside the engine, and a replay differs
    best = iv_exchange.Engine()
    for entry in [(0, 0, "a", "sell", 101, 5), (1, 0, "b", "sell", 100, 5), (2, 0, "c", "sell", 100, 5),
                  (3, 0, "d", "buy", 100, 7)]:
        best.apply(*entry)
    assert [(e[4], e[5], e[6]) for e in best.events if e[0] == "trade"] == [("b", 100, 5), ("c", 100, 2)]


def test_q39():
    assert 2_000_000 * 64 * 8 == 1_024_000_000
    assert 2_000_000 * 64 * 8 * 300 == pytest.approx(307e9, rel=0.01)
    assert 500_000 * 64 * 6.5 * 3600 == pytest.approx(748.8e9)
    assert 500_000 * 64 * 24 * 3600 == pytest.approx(2.7648e12)          # the same rate around the clock
    assert 500_000 * 64 * 6.5 * 3600 < 2_000_000 * 64 * 6.5 * 3600 and 24 / 6.5 == pytest.approx(2.7648e12 / 748.8e9)
    assert 2_000_000 * 0.0001 == 200


def test_q40():
    assert 5 * 252 * 10 * 25 == 315_000 and 315_000 / 1024 == pytest.approx(307.6, abs=0.1)  # GiB, then TiB
    assert 500 * 3 * 8 == 12_000 and 12_000 / 64 / 60 == pytest.approx(3.125)                # core-minutes, then hours
    assert 12_000 / 60 * 50 == 10_000 and 64 * 24 == 1536                                    # core-hours a day
