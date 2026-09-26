import pathlib
import random
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_binlog as bl  # noqa: E402
import make_binlog_fixtures as mk  # noqa: E402


def test_fixture_is_current_and_decodes_to_its_text():
    data = (HERE / "data/sample.blog").read_bytes()
    assert mk.sample().bytes() == data
    sites, recs = bl.read(data)
    assert bl.text(sites, recs) == (HERE / "data/sample.txt").read_text().splitlines()
    assert len(sites) == 5 and len(recs) == 17


def test_round_trip_of_random_statements():
    rng = random.Random(1)
    w = bl.Writer()
    want = []
    for k in range(500):
        a = (rng.randrange(-10**12, 10**12), rng.randrange(2**64), rng.random(), rng.choice("BSX"),
             "".join(rng.choice("abcXYZ") for _ in range(rng.randrange(20))))
        w.log(k, "{} {} {} {} {}", "iudcs", *a)
        want.append((k, (a[0], a[1], a[2], a[3], a[4][:16])))
    _, recs = bl.read(w.bytes())
    assert [(t, args) for t, _, args in recs] == want


def test_identifier_depends_on_types_and_collisions_are_refused():
    assert bl.site_id("x {}", "i") != bl.site_id("x {}", "u")
    w = bl.Writer()
    w.log(0, "a", "")
    w.sites[bl.site_id("b", "")] = ("a", "")          # plant a collision
    with pytest.raises(ValueError):
        w.log(0, "b", "")


def test_first_difference_bisects_two_logs():
    a = [(t, 1, (t % 7,)) for t in range(1000)]
    b = list(a)
    b[613] = (613, 1, (99,))
    assert bl.first_difference(a, b) == 613 and bl.first_difference(a, a) is None
    assert bl.first_difference(a, a[:900]) == 900


def test_journal_round_trip():
    ev = (HERE.parent / "bookbuilder/data/events_small.bin").read_bytes()
    recs = [(int.from_bytes(ev[i + 12:i + 20], "little") + 5_000, ev[i:i + 48]) for i in range(0, len(ev), 48)]
    data = bl.journal_write(recs)
    assert len(data) == 12 + 56 * 6_000 and bl.journal_read(data) == recs
