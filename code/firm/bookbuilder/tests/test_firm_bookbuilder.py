import csv
import math
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
FIRM = HERE.parent
for c in (HERE, FIRM / "feedhandler", FIRM / "feed", FIRM / "lobfeat"):
    sys.path.insert(0, str(c))
import firm_bookbuilder as bb  # noqa: E402
import firm_feed  # noqa: E402
import firm_feedhandler as fh  # noqa: E402
import make_book_fixtures as mk  # noqa: E402

DATA = HERE / "data"


def test_expected_is_current_and_invariants_hold():
    lines = (DATA / "expected.txt").read_text().splitlines()
    for line in lines:
        name, n, h = line.split()
        ev = mk.unpack((DATA / f"{name}.bin").read_bytes())
        assert len(ev) == int(n)
        book, hh = bb.Book(), bb.FNV_OFFSET
        for e in ev:
            book.apply(e)
            hh = bb.l2_hash(book, 5, hh)
            if not book.stale:
                assert book.check() == [], (name, e)
        assert f"{hh:016x}" == h


def test_same_level2_as_book1_feed():
    """Book 1's firm.feed book and this builder, fed the same order-by-order sample, agree on level 2 after every
    message."""
    raw = (FIRM / "feed/data/sample.itch").read_bytes()
    ref, book = firm_feed.Book(), bb.Book()
    i, n = 0, 0
    for m in firm_feed.decode(raw):
        ref.apply(m)
        length = int.from_bytes(raw[i:i + 2], "big")
        book.apply(fh.normalise(raw[i + 2:i + 2 + length], n))
        i += 2 + length
        n += 1
        for side, s in ((bb.B, "B"), (bb.S, "S")):
            assert book.depth(side, 10) == ref.depth(m.locate, s, 10)
    assert n > 1000


def test_same_top_of_book_as_book7_lobfeat():
    rows = list(csv.DictReader(open(FIRM / "lobfeat/data/fixture_msgs.csv")))
    want = list(csv.DictReader(open(FIRM / "lobfeat/data/fixture_expected.csv")))
    book = bb.Book()
    for k, (m, w) in enumerate(zip(rows, want, strict=True)):
        side = bb.B if m["side"] == "1" else bb.S
        kind = ord(m["kind"])
        book.apply((kind, side, 1, k, 0, int(m["oid"]), 0, int(m["price"]), int(m["qty"])))
        if w["bid"] != "nan":
            bid, bq, ask, aq = book.best()
            assert (bid, bq, ask, aq) == (int(float(w["bid"])), int(float(w["bid_qty"])), int(float(w["ask"])),
                                          int(float(w["ask_qty"])))


def test_replace_loses_priority_and_changes_reference():
    book = bb.Book()
    book.apply((ord("A"), bb.B, 1, 1, 0, 7, 0, 1000, 300))
    book.apply((ord("U"), 0, 1, 2, 0, 7, 8, 1001, 200))
    assert 7 not in book.orders and book.orders[8] == [bb.B, 1001, 200] and book.depth(bb.B, 2) == [(1001, 200)]


def test_recentring_model():
    assert bb.expected_recentrings(100, 800) == 0.25                    # sigma 100 ticks, a = 200 ticks
    rng = random.Random(3)
    # Monte Carlo over 400 days of 400 steps each, daily sigma 100 ticks, ladder 400 ticks (a = 100 ticks): the
    # long-run rate is sigma^2 / a^2 = 1 a day (monitoring 400 times a day overshoots a little and lowers it)
    x, path = 0.0, []
    for _ in range(400 * 400):
        x += rng.gauss(0, 100 / math.sqrt(400))
        path.append(round(x))
    rate = bb.recentrings(path, 400) / 400
    assert 0.8 < rate <= bb.expected_recentrings(100, 400)             # discrete monitoring can only lower it
    assert bb.daily_sigma_ticks(100.0, 0.02, 0.01) == 200.0
