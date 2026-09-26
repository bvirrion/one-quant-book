"""Chapter 24 helpers: the failover experiment of firm.sequencer over every cut point, and the arithmetic of the
weekend problem.

table() -> {(procedure, stage): (cut points, duplicates)}, and summary rows per procedure
duplicate_window_ns()     the part of an order's life during which a failure makes a fresh-identifier resend a copy
p_duplicate(orders_per_s, window_ns, fill_fraction)   probability that a failure at a random time duplicates an order
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/sequencer"))
import firm_sequencer as sq  # noqa: E402,F401
import firm_sequencer_sim as sim  # noqa: E402


def table():
    rows, summary = {}, []
    points = sim.cut_points()
    for proc in sim.PROCEDURES:
        rec, mx, dups = [], 0, 0
        for _, stage, t in points:
            o = sim.run(t, proc)
            n, d = rows.get((proc, stage), (0, 0))
            rows[(proc, stage)] = (n + 1, d + o.duplicates)
            rec.append(o.recovery_ns)
            mx = max(mx, o.max_abs_position)
            dups += o.duplicates
        summary.append((proc, len(points), dups, mx, min(rec), max(rec)))
    return rows, summary


def duplicate_window_ns():
    return 2 * sim.WIRE_NS                     # on the wire to the venue, then the report on its way back


def p_duplicate(orders_per_s, window_ns=None, fill_fraction=1.0):
    w = duplicate_window_ns() if window_ns is None else window_ns
    return orders_per_s * w * 1e-9 * fill_fraction
