"""firm.refdata -- the reference-data service (build of One Quant Book 15, chapter 6).

Vendors deliver facts about instruments -- 'from valid date v, field f of the instrument with external key k is x', each
known from the delivery that carried it -- and the service keeps all of them, bitemporally, in Book 7's firm.pit store.
Every external key (an ISIN, a vendor code) is mapped to a permanent identifier at first sight. A golden copy is built
per field by a precedence of vendors, with the vendor that supplied each value kept as its provenance, and every
disagreement between vendors is reported. Symbols resolve to permanent identifiers as of a date and as known at a
time. Corporate actions are events whose status changes (announced, confirmed, cancelled) are new versions, so the
adjustment factor between two dates is what was known when it is asked. A counterparty master keeps legal entities and
their parents the same way.

Dates and knowledge times are any comparable values (integers here: trading-day numbers).

API (stable):
    RefData(precedence: {field: (vendor, ...)})
        .ingest(vendor, known, valid, key, field, value)      a fact; returns the permanent id of `key`
        .pid(key) -> int
        .value(vendor, pid, field, valid, known)              the vendor's value in effect on `valid`, as known
        .golden(pid, field, valid, known) -> (value, vendor)  first vendor in precedence that has a value
        .conflicts(field, valid, known) -> [(pid, {vendor: value})]
        .resolve(field, value, valid, known) -> [pid]         instruments whose golden `field` equals `value`
        .add_action(event, pid, kind, ratio, effective, status, known)
        .actions(pid, known) -> [(event, kind, ratio, effective, status)]
        .factor(pid, start, end, known) -> float              product of confirmed split ratios in (start, end]
    CounterpartyMaster()
        .add(lei, name, parent, valid, known); .name(lei, valid, known); .ultimate_parent(lei, valid, known)
"""
from __future__ import annotations

import bisect
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "pit"))
from firm_pit import Store  # noqa: E402


class _Effective:
    """Effective-dated values in a firm.pit store: the value in effect on `valid` is the one
    of the latest valid date at or before it, each as known at `known`."""

    def __init__(self):
        self.store = Store()
        self.valids: dict[tuple, list] = {}

    def put(self, entity, field, valid, known, value) -> None:
        v = self.valids.setdefault((entity, field), [])
        if valid not in v:
            bisect.insort(v, valid)
        self.store.put(entity, field, valid, known, value)

    def get(self, entity, field, valid, known):
        v = self.valids.get((entity, field), [])
        for i in range(bisect.bisect_right(v, valid) - 1, -1, -1):
            x = self.store.asof(entity, field, v[i], known)
            if x is not None:
                return x
        return None


class RefData:
    def __init__(self, precedence: dict[str, tuple[str, ...]]):
        self.precedence = precedence
        self.facts = _Effective()
        self.keys: dict[str, int] = {}
        self.vendors: set[str] = set()
        self._actions: dict[int, dict] = {}

    def pid(self, key: str) -> int:
        return self.keys[key]

    def ingest(self, vendor: str, known, valid, key: str, field: str, value) -> int:
        pid = self.keys.setdefault(key, len(self.keys) + 1)
        self.vendors.add(vendor)
        self.facts.put((pid, vendor), field, valid, known, value)
        return pid

    def value(self, vendor: str, pid: int, field: str, valid, known):
        return self.facts.get((pid, vendor), field, valid, known)

    def golden(self, pid: int, field: str, valid, known):
        order = self.precedence.get(field, tuple(sorted(self.vendors)))
        for vendor in order:
            x = self.value(vendor, pid, field, valid, known)
            if x is not None:
                return x, vendor
        return None, None

    def conflicts(self, field: str, valid, known) -> list:
        out = []
        for pid in sorted(set(self.keys.values())):
            vals = {v: self.value(v, pid, field, valid, known)
                    for v in sorted(self.vendors)}
            vals = {v: x for v, x in vals.items() if x is not None}
            if len(set(vals.values())) > 1:
                out.append((pid, vals))
        return out

    def resolve(self, field: str, value, valid, known) -> list[int]:
        return [pid for pid in sorted(set(self.keys.values())) if self.golden(pid, field, valid, known)[0] == value]

    # ------------------------------------------------------------------ corporate actions
    def add_action(self, event: str, pid: int, kind: str, ratio: float, effective,
                   status: str, known) -> None:
        """A new version of event `event`: announced, confirmed or cancelled; the latest
        version known wins."""
        versions = self._actions.setdefault(pid, {}).setdefault(event, [])
        versions.append((known, kind, ratio, effective, status))
        self._actions[pid][event].sort(key=lambda r: r[0])

    def actions(self, pid: int, known) -> list:
        out = []
        for event, versions in self._actions.get(pid, {}).items():
            live = [r for r in versions if r[0] <= known]
            if live:
                _, kind, ratio, effective, status = live[-1]
                out.append((event, kind, ratio, effective, status))
        return sorted(out, key=lambda r: (r[3], r[0]))

    def factor(self, pid: int, start, end, known) -> float:
        """Price adjustment factor for splits effective after `start` and at or before `end`,
        as known: a price at `start` divided by this factor is comparable with prices at
        `end`."""
        f = 1.0
        for _event, kind, ratio, effective, status in self.actions(pid, known):
            if kind == "split" and status == "confirmed" and start < effective <= end:
                f *= ratio
        return f


class CounterpartyMaster:
    """Legal entities by LEI: name and parent entity, effective-dated and bitemporal."""

    def __init__(self):
        self.facts = _Effective()

    def add(self, lei: str, name: str, parent: str | None, valid, known) -> None:
        self.facts.put(lei, "name", valid, known, name)
        self.facts.put(lei, "parent", valid, known, parent or "")

    def name(self, lei: str, valid, known):
        return self.facts.get(lei, "name", valid, known)

    def ultimate_parent(self, lei: str, valid, known) -> str:
        seen = [lei]
        while True:
            p = self.facts.get(seen[-1], "parent", valid, known)
            if not p or p in seen:
                return seen[-1]
            seen.append(p)
