"""Write firm.ordergw's fixtures: two journals of the gateway against Book 10's matching engine (seeded), which the C++
and Rust gateways replay, and the Python reference's summary of each.

data/journal_cancel.txt    300 cycles, cancel latency 100 us, fills at 200 a second, cancel then new
data/journal_replace.txt   the same with cancel-replace and a throttle of 300 messages a second (burst 2)
data/expected.txt          one summary line per journal
data/table.txt             the state table, one "state event next" line per allowed transition
Journal lines: "t Q N cl side qty price result", "t Q X cl result", "t Q U cl new_cl qty price result",
"t R kind cl qty price leaves reason new_cl" (reason '-' when none).
"""
import pathlib

import firm_ordergw as gw
import firm_ordergw_sim as sim

HERE = pathlib.Path(__file__).resolve().parent
RUNS = {"cancel": dict(mode="cancel"), "replace": dict(mode="replace", rate=300, burst=2)}


def main():
    lines = []
    for name, kw in RUNS.items():
        r = sim.run(7, 100_000, 200.0, 300, **kw)
        (HERE / "data" / f"journal_{name}.txt").write_text("\n".join(r.journal) + "\n")
        lines.append(f"{name} {gw.summary(r.gateway)}")
    (HERE / "data/expected.txt").write_text("\n".join(lines) + "\n")
    (HERE / "data/table.txt").write_text("".join(f"{s} {e} {n}\n" for (s, e), n in sorted(gw.TABLE.items())))


if __name__ == "__main__":
    main()
