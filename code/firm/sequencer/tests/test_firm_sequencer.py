import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_sequencer as sq  # noqa: E402
import firm_sequencer_sim as sim  # noqa: E402
import make_sequencer_fixtures as mk  # noqa: E402


def test_fixture_is_current_and_replays_to_its_states():
    lines = (HERE / "data/journal.txt").read_text().splitlines()
    entries = [sq.from_line(x) for x in lines]
    assert entries == mk.failover_journal()
    assert [sq.to_line(e) for e in entries] == lines
    want = (HERE / "data/expected.txt").read_text().splitlines()
    assert mk.states(entries, {int(w.split()[1]) for w in want}) == want


def test_fencing():
    j = sq.Journal()
    j.append(1, "M", 1_000_000)
    j.fence(2)
    with pytest.raises(ValueError):
        j.append(1, "M", 1_000_100)                   # the old primary, not quite dead
    assert j.append(2, "M", 1_000_200) == 2
    with pytest.raises(ValueError):
        j.fence(2)


def test_replicas_agree_and_gaps_are_refused():
    entries = mk.failover_journal()
    a, b = sq.Replica(), sq.Replica()
    for e in entries:
        assert a.apply(e) == b.apply(e) and a.hash == b.hash
    with pytest.raises(ValueError):
        sq.Replica().apply(entries[1])


def test_failure_free_run():
    o = sim.run(None)
    assert o.duplicates == 0 and o.replay_equal and o.position == o.venue_position
    assert o.max_abs_position <= sq.LIMIT and o.orders == len(o.order_times) == 46


@pytest.mark.parametrize("procedure", sim.PROCEDURES)
def test_every_cut_point(procedure):
    """At every stage of every order: the backup's state equals a replay of the journal and the venue's position;
    duplicates occur only with fresh identifiers and without reconciliation, while the order is between the wire and
    the journal."""
    dups = {}
    for k, stage, t in sim.cut_points():
        o = sim.run(t, procedure)
        assert o.replay_equal and o.position == o.venue_position, (k, stage)
        assert 2_700_000 <= o.recovery_ns <= 3_100_000
        dups[stage] = dups.get(stage, 0) + o.duplicates
    if procedure == "fresh ids":
        assert dups == {"journaled, not yet sent": 0, "sent, in flight": 27, "at the venue, not yet reported": 27,
                        "reported": 0}
    else:
        assert set(dups.values()) == {0}
