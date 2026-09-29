"""firm.paramstore -- typed parameters, approvals, history, flags and a signal service (One Quant Book 15, chapter 16).

Every production parameter has a schema: a canonical unit, the units it may be entered in (with their factors), bounds,
the largest change allowed in one step, and the change above which two approvers other than the author are needed. A
change is proposed with a value and a unit; it is converted to the canonical unit and checked against the schema, and
refused with its reasons, or held until approved, then stored with its effective (valid) time and its recorded
(knowledge) time, so that the store answers what was live at any moment as it was known at any moment. Every action goes
to Book 12's hash-chained audit trail (firm.exptrack.AuditTrail). Feature flags roll a new value out to named strategies
first. Drift compares the configuration the store declares with what each strategy reports it is running. The signal
service serves versioned research signals with a freshness bound and a declared fallback.

API (stable):
    Schema(name, unit, units={unit: factor}, lo, hi, max_step=inf, two_approvals_above=inf)
    ParamStore(root)   .register(schema) ; .propose(strategy, name, value, unit, effective, recorded, author) -> Change
                       .approve(change_id, approver, ts) -> Change ; .as_of(strategy, name, valid, known=None) -> value
                       .history(strategy, name) -> [(effective, recorded, value, change_id)] ; .audit.verify() -> -1 ok
    Change: cid, status ('refused', 'pending', 'applied'), reasons, canonical value, approvals
    Flags().set(flag, strategies) ; .on(flag, strategy) -> bool
    drift(declared {strategy: {name: value}}, running {strategy: {name: value}}, tol=0) -> [(strategy, name, d, r)]
    SignalService(max_age, fallback)  .publish(name, value, version, ts) ; .get(name, now) -> (value, version, status)
        status 'fresh', 'stale-fallback' (the declared fallback), or 'missing-fallback'
"""
from __future__ import annotations

import math
import pathlib
import sys
from dataclasses import dataclass, field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "exptrack"))
from firm_exptrack import AuditTrail  # noqa: E402


@dataclass(frozen=True)
class Schema:
    name: str
    unit: str                           # canonical unit
    units: dict                         # accepted input units -> factor to the canonical unit
    lo: float
    hi: float
    max_step: float = math.inf          # largest change in one step, canonical units
    two_approvals_above: float = math.inf


@dataclass
class Change:
    cid: int
    strategy: str
    name: str
    value: float                        # canonical
    entered: str                        # as typed, with its unit
    effective: float
    recorded: float
    author: str
    status: str = "pending"
    reasons: list = field(default_factory=list)
    approvals: list = field(default_factory=list)
    needed: int = 0


class ParamStore:
    def __init__(self, root):
        root = pathlib.Path(root)
        root.mkdir(parents=True, exist_ok=True)
        self.audit = AuditTrail(root / "audit.jsonl")
        self.schemas: dict = {}
        self.changes: list[Change] = []
        self.rows: dict = {}            # (strategy, name) -> [(effective, recorded, value, cid)]

    def register(self, schema: Schema) -> None:
        self.schemas[schema.name] = schema
        body = {"name": schema.name, "unit": schema.unit, "lo": schema.lo, "hi": schema.hi}
        self.audit.append("schema", body, 0)

    def propose(self, strategy, name, value, unit, effective, recorded, author) -> Change:
        s = self.schemas[name]
        c = Change(len(self.changes), strategy, name, math.nan, f"{value} {unit}",
                   effective, recorded, author)
        self.changes.append(c)
        if unit not in s.units:
            c.reasons.append(f"unit {unit!r} not accepted for {name} "
                             f"(accepted: {', '.join(s.units)})")
        else:
            c.value = float(value) * s.units[unit]
            if not s.lo <= c.value <= s.hi:
                c.reasons.append(f"{c.value:g} {s.unit} outside [{s.lo:g}, {s.hi:g}]")
            old = self.as_of(strategy, name, recorded, recorded)
            step = abs(c.value - old) if old is not None else 0.0
            if step > s.max_step:
                c.reasons.append(f"step {step:g} {s.unit} above the allowed {s.max_step:g}")
            c.needed = 2 if step > s.two_approvals_above else 1
        c.status = "refused" if c.reasons else "pending"
        body = {"cid": c.cid, "strategy": strategy, "name": name, "entered": c.entered,
                "status": c.status, "reasons": c.reasons}
        self.audit.append("propose", body, recorded)
        return c

    def approve(self, cid: int, approver: str, ts: float) -> Change:
        c = self.changes[cid]
        if c.status != "pending" or approver == c.author or approver in c.approvals:
            self.audit.append("approve-refused", {"cid": cid, "approver": approver}, ts)
            return c
        c.approvals.append(approver)
        self.audit.append("approve", {"cid": cid, "approver": approver}, ts)
        if len(c.approvals) >= c.needed:
            c.status = "applied"
            rec = max(ts, c.recorded)
            row = (c.effective, rec, c.value, cid)
            self.rows.setdefault((c.strategy, c.name), []).append(row)
            body = {"cid": cid, "value": c.value, "effective": c.effective}
            self.audit.append("apply", body, rec)
        return c

    def as_of(self, strategy, name, valid, known=None):
        """The value in force at `valid`, as the store knew it at `known` (default: now)."""
        rows = self.rows.get((strategy, name), [])
        rows = [r for r in rows if r[0] <= valid and (known is None or r[1] <= known)]
        if not rows:
            return None
        return max(rows, key=lambda r: (r[0], r[1]))[2]

    def history(self, strategy, name):
        return sorted(self.rows.get((strategy, name), []))


class Flags:
    def __init__(self):
        self.flags: dict = {}

    def set(self, flag: str, strategies) -> None:
        self.flags[flag] = set(strategies)

    def on(self, flag: str, strategy: str) -> bool:
        return strategy in self.flags.get(flag, set())


def drift(declared: dict, running: dict, tol: float = 0.0) -> list:
    out = []
    for strat in sorted(set(declared) | set(running)):
        d, r = declared.get(strat, {}), running.get(strat, {})
        for name in sorted(set(d) | set(r)):
            a, b = d.get(name), r.get(name)
            if a is None or b is None or abs(a - b) > tol:
                out.append((strat, name, a, b))
    return out


class SignalService:
    """Versioned values; a reader gets the latest if fresh, else the declared fallback."""

    def __init__(self, max_age: float, fallback: float):
        self.max_age, self.fallback = max_age, fallback
        self.values: dict = {}                 # name -> [(ts, version, value)]

    def publish(self, name: str, value: float, version: str, ts: float) -> None:
        self.values.setdefault(name, []).append((ts, version, value))

    def get(self, name: str, now: float):
        vals = [v for v in self.values.get(name, []) if v[0] <= now]
        if not vals:
            return self.fallback, None, "missing-fallback"
        ts, version, value = max(vals)
        if now - ts > self.max_age:
            return self.fallback, version, "stale-fallback"
        return value, version, "fresh"
