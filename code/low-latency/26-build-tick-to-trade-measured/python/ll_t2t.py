"""Chapter 26 helpers: the stages of the assembled path, computed from the stamps of the live harness, their
quantiles, and chapter 1's three-microsecond budget as a firm.latbudget Budget.

STAGES            (name, from stamp, to stamp): the boundaries of chapter 26's figure
stage_samples(rows) -> {stage: ndarray of ns}  rows: dicts of the harness's stamps (ns)
budget()          chapter 1's example: 0.9 us receive, 60 ns decode, 120 ns book, 200 ns strategy, 50 ns risk,
                  0.8 us transmit, 3 us end to end, all at the median
"""
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/latbudget"))
import firm_latbudget as lb  # noqa: E402

STAMPS = ("exch", "recv", "pub", "pop", "book", "decide", "risk", "encode", "sent", "venue")
STAGES = (("receive", "exch", "recv"), ("decode", "recv", "pub"), ("ring", "pub", "pop"), ("book", "pop", "book"),
          ("strategy", "book", "decide"), ("risk", "decide", "risk"), ("gateway", "risk", "encode"),
          ("transmit", "encode", "venue"))
TOTALS = (("tick to trade", "exch", "venue"), ("in process", "recv", "encode"))


def stage_samples(rows):
    """Per-stage samples from the first order of each event (a second order waits for the first one's send, which
    would be charged to its risk stage); the totals from every order."""
    first = [r for r in rows if int(r["nth"]) == 0]
    out = {}
    for name, a, b in STAGES:
        out[name] = np.array([float(r[b]) - float(r[a]) for r in first])
    for name, a, b in TOTALS:
        out[name] = np.array([float(r[b]) - float(r[a]) for r in rows])
    return out


def budget():
    return lb.Budget([lb.Stage("receive", {0.5: 900}), lb.Stage("decode", {0.5: 60}), lb.Stage("ring", {}),
                      lb.Stage("book", {0.5: 120}), lb.Stage("strategy", {0.5: 200}), lb.Stage("risk", {0.5: 50}),
                      lb.Stage("gateway", {}), lb.Stage("transmit", {0.5: 800})], {0.5: 3_000})
