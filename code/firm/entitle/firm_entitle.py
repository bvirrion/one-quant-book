"""firm.entitle -- in-process market-data distribution, entitlements, usage logs and audits (Book 15, ch. 23).

A distribution platform takes a normalised feed and delivers it inside the firm to screens, strategies, risk services
and research jobs. Here the bus holds one queue per subscriber, either every update in order ('all') or only the
latest update per topic ('conflate'), and it is simulated in virtual time: each subscriber takes a fixed time per
message, so queue depths and the age of what each subscriber sees follow from the update times. Every subscription is
checked against the entitlement system at subscribe time and, when `check_on_delivery`, again at every delivery, so
that a revocation takes effect at once. Every access is written to a usage log; the monthly usage report counts by
the venue's unit of count (display: user identifiers; non-display: devices), and the audit reconciles months of usage
with the licences held and prices the shortfall with a fee schedule.

API (stable):
    Entitlement(subject, source, use)           use: 'display' or 'non-display'
    EntitlementSystem(): .grant(e, at) ; .revoke(e, at) ; .check(subject, source, use, at) -> bool
    Bus(ents, check_on_delivery=True, trace_every=0)
        .subscribe(name, subject, source, use, topics, service, policy, at) -> bool (entitled?)
        .run(updates [(ts, topic, value)]) -> {name: Stats(delivered, max_depth, mean_age, max_age, denied, trace)}
    UsageLog(): .record(month, source, use, unit_id, subject)
    usage_report(log, month, source) -> {'display': n, 'non-display': n}
    audit(log, source, months, licensed {use: n}, fees {use: callable(n) -> monthly fee}) -> [AuditRow]
"""
from __future__ import annotations

import heapq
from collections import OrderedDict, deque
from dataclasses import dataclass, field

USES = ("display", "non-display")


@dataclass(frozen=True)
class Entitlement:
    subject: str                     # a user identifier or an application
    source: str                      # a venue's product, e.g. a depth feed
    use: str                         # 'display' or 'non-display'


class EntitlementSystem:
    """Grants and revocations with their times; a check answers as of a time."""

    def __init__(self):
        self.events: list = []       # (at, +1 grant / -1 revoke, entitlement)

    def grant(self, e: Entitlement, at: float = 0.0) -> None:
        self.events.append((at, 1, e))

    def revoke(self, e: Entitlement, at: float) -> None:
        self.events.append((at, -1, e))

    def check(self, subject: str, source: str, use: str, at: float) -> bool:
        e = Entitlement(subject, source, use)
        state = False
        for t, sign, x in sorted(self.events, key=lambda r: r[0]):
            if t > at:
                break
            if x == e:
                state = sign > 0
        return state


@dataclass
class Stats:
    delivered: int = 0
    max_depth: int = 0
    mean_age: float = 0.0
    max_age: float = 0.0
    denied: int = 0
    trace: list = field(default_factory=list)     # (delivery time, age), every `trace_every`-th


@dataclass
class _Sub:
    name: str
    subject: str
    source: str
    use: str
    topics: set
    service: float                   # seconds of work per message
    policy: str                      # 'all' or 'conflate'
    queue: object = None
    busy_until: float = 0.0
    stats: Stats = field(default_factory=Stats)
    ages: list = field(default_factory=list)


class Bus:
    def __init__(self, ents: EntitlementSystem, check_on_delivery: bool = True, trace_every: int = 0):
        self.ents, self.check_on_delivery, self.subs = ents, check_on_delivery, []
        self.trace_every = trace_every

    def subscribe(self, name, subject, source, use, topics, service, policy="all", at=0.0) -> bool:
        if not self.ents.check(subject, source, use, at):
            return False
        q = OrderedDict() if policy == "conflate" else deque()
        self.subs.append(_Sub(name, subject, source, use, set(topics), service, policy, q))
        return True

    def _enqueue(self, s: _Sub, ts: float, topic: str, value) -> None:
        if s.policy == "conflate":
            s.queue.pop(topic, None)             # keep only the latest per topic
            s.queue[topic] = (ts, value)
        else:
            s.queue.append((ts, topic, value))
        s.stats.max_depth = max(s.stats.max_depth, len(s.queue))

    def _pop(self, s: _Sub):
        if s.policy == "conflate":
            _topic, (ts, value) = s.queue.popitem(last=False)
            return ts, value
        ts, _topic, value = s.queue.popleft()
        return ts, value

    def run(self, updates) -> dict:
        """Deliver `updates` (time-ordered) to every subscriber; each is served one message
        at a time, `service` seconds each, oldest topic first."""
        ready = []                                  # (time a subscriber becomes free, index)
        for u_ts, topic, value in list(updates) + [(float("inf"), None, None)]:
            while ready and ready[0][0] <= u_ts:     # serve every delivery due before this update
                t, i = heapq.heappop(ready)
                self._serve(self.subs[i], t, ready, i)
            if topic is None:
                break
            for i, s in enumerate(self.subs):
                if topic in s.topics:
                    was_empty = not s.queue
                    self._enqueue(s, u_ts, topic, value)
                    if was_empty:                   # no delivery pending: schedule one
                        heapq.heappush(ready, (max(u_ts, s.busy_until), i))
        for s in self.subs:
            s.stats.mean_age = sum(s.ages) / len(s.ages) if s.ages else 0.0
        return {s.name: s.stats for s in self.subs}

    def _serve(self, s: _Sub, t: float, ready: list, i: int) -> None:
        if not s.queue:
            return
        ts, _value = self._pop(s)
        if self.check_on_delivery and not self.ents.check(s.subject, s.source, s.use, t):
            s.stats.denied += 1
        else:
            s.stats.delivered += 1
            s.ages.append(t + s.service - ts)
            s.stats.max_age = max(s.stats.max_age, t + s.service - ts)
            if self.trace_every and s.stats.delivered % self.trace_every == 0:
                s.stats.trace.append((t + s.service, t + s.service - ts))
        s.busy_until = t + s.service
        if s.queue:
            heapq.heappush(ready, (s.busy_until, i))


# ------------------------------------------------------------ usage, reports, audits
@dataclass(frozen=True)
class Usage:
    month: int
    source: str
    use: str
    unit_id: str                     # user identifier (display) or device (non-display)
    subject: str


class UsageLog:
    def __init__(self):
        self.rows: list[Usage] = []

    def record(self, month: int, source: str, use: str, unit_id: str, subject: str) -> None:
        self.rows.append(Usage(month, source, use, unit_id, subject))


def usage_report(log: UsageLog, month: int, source: str) -> dict:
    """The monthly count a venue asks for: distinct units of count by use."""
    units = {u: set() for u in USES}
    for r in log.rows:
        if r.month == month and r.source == source:
            units[r.use].add(r.unit_id)
    return {u: len(v) for u, v in units.items()}


@dataclass
class AuditRow:
    month: int
    used: dict
    licensed: dict
    shortfall: dict
    owed: float


def audit(log: UsageLog, source: str, months, licensed: dict, fees: dict) -> list[AuditRow]:
    """Reconcile each month's usage with the licences held; the amount owed is the fee for
    what was used minus the fee for what was licensed, by use."""
    out = []
    for m in months:
        used = usage_report(log, m, source)
        short = {u: max(0, used[u] - licensed.get(u, 0)) for u in USES}
        owed = sum(max(0.0, fees[u](used[u]) - fees[u](licensed.get(u, 0))) for u in USES)
        out.append(AuditRow(m, used, dict(licensed), short, owed))
    return out
