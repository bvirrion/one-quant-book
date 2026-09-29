"""firm.dataqual -- data-quality rules, flags, quarantine, corrections and lineage (build of One Quant Book 15, ch. 7).

Rules are data: a name, a kind, a severity, an owner and parameters. Running them over a partition of the tick store
produces flags -- (table, row, rule, severity, detail) -- and never deletes or edits a row: consumers choose to exclude
flagged rows, and a partition with an error-severity flag is quarantined until someone releases it. Corrections from a
vendor are new versions of a fact (Book 7's firm.pit), never overwrites. A lineage graph records, for every dataset
version, the content hash of the data and of each input it was derived from (Book 7's firm.workflow.content_hash), so
that a correction names every downstream result that is now stale.

Rule kinds (params):
    sequence      gaps in an integer sequence column                     (column)
    bounds        values outside [lo, hi]                                (column, lo, hi)
    crossed       bid at or above ask                                    (bid, ask)
    spike         |log value - median of the previous window| more than k robust deviations (floored), per symbol
                                                                         (column, k, window, floor, confirm, by)
    stale         a gap between consecutive rows of a symbol longer than max_gap, outside exempt windows
                                                                         (time, max_gap, by, exempt)
    cross_source  per time bucket, a count that differs from a reference source by more than tol
                                                                         (time, bucket, tol, reference)
    busted        rows whose key is in a list of broken trades           (key, busted)

API (stable):
    Rule(name, kind, severity='warning', owner='', params={})
    Flag(table, row, rule, severity, detail)
    run(rules_by_table: {table: [Rule]}, tables: {table: pandas.DataFrame}) -> [Flag]
    clean(df, flags, table, severities=('error', 'warning')) -> DataFrame without the flagged rows
    Quarantine(): .apply(partition, flags) -> state; .release(partition, by, reason); .readable(partition); .log
    Lineage(): .add(name, data, inputs=(), code='') -> (name, hash); .downstream(node); .stale_after(name, old)
"""
from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "workflow"))
from firm_workflow import content_hash  # noqa: E402


@dataclass(frozen=True)
class Rule:
    name: str
    kind: str
    severity: str = "warning"
    owner: str = ""
    params: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Flag:
    table: str
    row: int
    rule: str
    severity: str
    detail: str


def _rows_sequence(df, p):
    s = df[p["column"]].to_numpy()
    jumps = np.flatnonzero(np.diff(s) > 1)
    return [(int(df.index[i + 1]), f"gap of {int(s[i + 1] - s[i] - 1)} after {int(s[i])}") for i in jumps]


def _rows_bounds(df, p):
    v = df[p["column"]]
    bad = df.index[(v < p["lo"]) | (v > p["hi"])]
    return [(int(i), f"{p['column']}={df.at[i, p['column']]}") for i in bad]


def _rows_crossed(df, p):
    bad = df.index[df[p["bid"]] >= df[p["ask"]]]
    return [(int(i), f"bid {df.at[i, p['bid']]} >= ask {df.at[i, p['ask']]}") for i in bad]


def _rows_spike(df, p):
    """Deviation of each value from the median of the previous `window` values of its
    symbol, in robust units: the median absolute deviation of those previous deviations,
    floored at `floor` (a relative move below which nothing is a spike, e.g. a tick). With
    `confirm`, the value must also deviate from the median of the next `window` values: a
    spike comes back, a genuine move of the level does not (a batch check may look ahead)."""
    out = []
    w, k, floor = p["window"], p["k"], p.get("floor", 1e-3)
    for _, g in df.groupby(p.get("by", "symbol"), sort=False):
        x = np.log(g[p["column"]].astype(float))
        behind = x.rolling(w, min_periods=5).median().shift(1)
        ahead = x[::-1].rolling(w, min_periods=5).median().shift(1)[::-1]
        dev = x - behind.fillna(ahead)       # a day's first rows have no history: look ahead
        mad = dev.abs().rolling(w, min_periods=5).median().shift(1).fillna(0.0)
        scale = np.maximum(1.4826 * mad, floor)
        z = dev / scale
        hit = z.abs() > k
        if p.get("confirm"):
            hit &= ((x - ahead.fillna(behind)) / scale).abs() > k
        for i in g.index[hit]:
            out.append((int(i), f"robust z {z[i]:.1f}"))
    return out


def _rows_stale(df, p):
    """Gaps longer than max_gap between consecutive rows of a symbol, not counting the time
    inside the `exempt` windows [(symbol, t0, t1)] in which the market itself was silent (a
    trading halt, a scheduled pause)."""
    out = []
    exempt = p.get("exempt", ())
    for sym, g in df.groupby(p.get("by", "symbol"), sort=False):
        t = g[p["time"]].to_numpy()
        for k in np.flatnonzero(np.diff(t) > p["max_gap"]):
            quiet = sum(max(0, min(t[k + 1], t1) - max(t[k], t0))
                        for s, t0, t1 in exempt if s == sym)
            if t[k + 1] - t[k] - quiet <= p["max_gap"]:     # the market's state explains it
                continue
            gap = (t[k + 1] - t[k]) / 1e9
            out.append((int(g.index[k + 1]), f"no update for {gap:.1f} s"))
    return out


def _rows_cross_source(df, p):
    ref = p["reference"]
    b = p["bucket"]
    mine = df[p["time"]].floordiv(b).value_counts()
    theirs = ref[p["time"]].floordiv(b).value_counts()
    buckets = sorted(set(mine.index) | set(theirs.index))
    out = []
    for k in buckets:
        m, r = int(mine.get(k, 0)), int(theirs.get(k, 0))
        if abs(m - r) > p["tol"] * max(r, 1):
            rows = df.index[df[p["time"]].floordiv(b) == k]
            out.append((int(rows[0]) if len(rows) else -1, f"bucket {k}: {m} rows against {r} in the reference"))
    return out


def _rows_busted(df, p):
    bad = df.index[df[p["key"]].isin(set(p["busted"]))]
    return [(int(i), f"broken trade {df.at[i, p['key']]}") for i in bad]


KINDS = {"sequence": _rows_sequence, "bounds": _rows_bounds, "crossed": _rows_crossed, "spike": _rows_spike,
         "stale": _rows_stale, "cross_source": _rows_cross_source, "busted": _rows_busted}


def run(rules_by_table: dict, tables: dict) -> list[Flag]:
    flags = []
    for table, rules in rules_by_table.items():
        df = tables[table]
        for r in rules:
            for row, detail in KINDS[r.kind](df, r.params):
                flags.append(Flag(table, row, r.name, r.severity, detail))
    return flags


def clean(df: pd.DataFrame, flags: list[Flag], table: str, severities=("error", "warning")) -> pd.DataFrame:
    drop = {f.row for f in flags if f.table == table and f.severity in severities and f.row >= 0}
    return df.drop(index=[i for i in drop if i in df.index])


class Quarantine:
    """Partition states: 'published', 'quarantined' (an error flag), 'released' (by a person, with a reason)."""

    def __init__(self):
        self.state: dict[str, str] = {}
        self.log: list[tuple] = []

    def apply(self, partition: str, flags: list[Flag]) -> str:
        errors = [f for f in flags if f.severity == "error"]
        self.state[partition] = "quarantined" if errors else "published"
        self.log.append((partition, self.state[partition], f"{len(errors)} error flags", "rules"))
        return self.state[partition]

    def release(self, partition: str, by: str, reason: str) -> None:
        if self.state.get(partition) != "quarantined":
            raise ValueError(f"{partition} is not quarantined")
        self.state[partition] = "released"
        self.log.append((partition, "released", reason, by))

    def readable(self, partition: str) -> bool:
        return self.state.get(partition) in ("published", "released")


class Lineage:
    """Dataset versions as nodes (name, content hash); an edge from every input version to the output version."""

    def __init__(self):
        self.inputs: dict[tuple, tuple] = {}
        self.code: dict[tuple, str] = {}

    def add(self, name: str, data, inputs=(), code: str = "") -> tuple:
        node = (name, content_hash(data))
        self.inputs[node] = tuple(inputs)
        self.code[node] = code
        return node

    def downstream(self, node: tuple) -> set:
        out, todo = set(), [node]
        while todo:
            n = todo.pop()
            for m, ins in self.inputs.items():
                if n in ins and m not in out:
                    out.add(m)
                    todo.append(m)
        return out

    def upstream(self, node: tuple) -> set:
        out, todo = set(), [node]
        while todo:
            for m in self.inputs.get(todo.pop(), ()):
                if m not in out:
                    out.add(m)
                    todo.append(m)
        return out

    def stale_after(self, name: str, old_hash: str) -> set:
        """Every dataset version built, directly or not, from the old version of `name`."""
        return self.downstream((name, old_hash))
