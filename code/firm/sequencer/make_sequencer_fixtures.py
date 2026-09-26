"""Write firm.sequencer's fixture: the journal of a failover (the primary fails while an order is in flight, the
backup resends under fresh identifiers, so the journal holds aliases, a second epoch and a duplicate), and the states a
replica reaches on its prefixes, which the C++ and Rust replicas must reproduce.

data/journal.txt    one entry per line: epoch seq kind fields
data/expected.txt   "prefix n hash position open unacknowledged-keys" for a few prefixes and the whole journal
"""
import pathlib

import firm_sequencer as sq
import firm_sequencer_sim as sim

HERE = pathlib.Path(__file__).resolve().parent


def failover_journal():
    k, stage, t = next(p for p in sim.cut_points() if p[1] == "sent, in flight" and p[0] == 3)
    return sim.run(t, "fresh ids").journal


def states(entries, prefixes):
    r = sq.Replica()
    out = []
    for i, e in enumerate(entries, 1):
        r.apply(e)
        if i in prefixes:
            keys = ",".join(f"{a}.{b}" for (a, b), _ in r.unacknowledged()) or "-"
            out.append(f"prefix {i} {r.hash:016x} {r.position} {len(r.open)} {keys}")
    return out


def main():
    entries = failover_journal()
    (HERE / "data/journal.txt").write_text("\n".join(map(sq.to_line, entries)) + "\n")
    prefixes = {10, 50, 100, 150, len(entries)}
    (HERE / "data/expected.txt").write_text("\n".join(states(entries, prefixes)) + "\n")


if __name__ == "__main__":
    main()
