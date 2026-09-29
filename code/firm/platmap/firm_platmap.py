"""firm.platmap -- the platform map as data (build of One Quant Book 15, chapter 1).

A platform map lists the firm's systems, the datasets they hold, and the jobs that turn datasets into other datasets,
with the clock each one runs on. Everything is data, so the map can be checked and questioned: does every dataset
have exactly one system of record, is the batch free of cycles, what does a late or wrong input reach, when must each
job start for the morning's reports to be ready, and which job reads an input before it is complete.

Times are minutes after the day's close (16:00 local = 0; 07:00 the next morning = 900).

API (stable):
    System(name, layer, owner)
    Dataset(name, system, cadence='batch'|'stream', ready=None)   ready: arrival time of an external input
    Job(name, inputs, outputs, duration, start=None, deadline=None)
        start=None: runs when its last input is ready (dependency-driven); a number: fixed clock start
    PlatformMap(systems, datasets, jobs)
        .validate() -> list[str]                  problems: systems of record, unknown names, producers, cycles
        .producer(dataset) -> Job | None
        .downstream(name) -> set[str]             every dataset reached from a dataset (closure)
        .upstream(name) -> set[str]               every dataset a dataset depends on
        .schedule(arrivals=None) -> dict          job -> (start, end); arrivals override Dataset.ready
        .ready_times(arrivals=None) -> dict       dataset -> time its complete version is ready
        .stale_reads(arrivals=None) -> list       (job, dataset, start, ready): a fixed-start job reading early
        .latest_starts(deadline) -> dict          job -> latest start that still meets every deadline
        .slack(deadline, arrivals=None) -> dict   job -> latest start - scheduled start
        .longest_chain(arrivals=None) -> list     the chain of jobs that ends last (names, in order)
        .blast_radius() -> dict                   external input -> number of datasets downstream
    hhmm(minutes) -> 'HH:MM' (minutes after 16:00)
"""
from __future__ import annotations

from dataclasses import dataclass, field

CLOSE_MIN = 16 * 60


def hhmm(t: float) -> str:
    m = int(round(CLOSE_MIN + t)) % (24 * 60)
    return f"{m // 60:02d}:{m % 60:02d}"


@dataclass(frozen=True)
class System:
    name: str
    layer: str
    owner: str = ""


@dataclass(frozen=True)
class Dataset:
    name: str
    system: str | tuple[str, ...]          # its system of record; a tuple is a conflict validate() reports
    cadence: str = "batch"
    ready: float | None = None             # external input: time it arrives complete


@dataclass(frozen=True)
class Job:
    name: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    duration: float
    start: float | None = None             # None: dependency-driven; a number: fixed clock start
    deadline: float | None = None          # its outputs are needed by then


@dataclass
class PlatformMap:
    systems: list[System]
    datasets: list[Dataset]
    jobs: list[Job]
    _ds: dict = field(init=False, repr=False)
    _jobs: dict = field(init=False, repr=False)

    def __post_init__(self):
        self._ds = {d.name: d for d in self.datasets}
        self._jobs = {j.name: j for j in self.jobs}

    # ------------------------------------------------------------------ structure
    def producer(self, dataset: str) -> Job | None:
        for j in self.jobs:
            if dataset in j.outputs:
                return j
        return None

    def validate(self) -> list[str]:
        out = []
        sysnames = {s.name for s in self.systems}
        for d in self.datasets:
            owners = d.system if isinstance(d.system, tuple) else (d.system,)
            if len(owners) != 1:
                names = ", ".join(owners)
                out.append(f"{d.name}: {len(owners)} systems of record ({names})")
            for o in owners:
                if o not in sysnames:
                    out.append(f"{d.name}: unknown system {o}")
            makers = [j.name for j in self.jobs if d.name in j.outputs]
            if d.ready is None and not makers:
                out.append(f"{d.name}: no producer and no arrival time")
            if len(makers) > 1:
                out.append(f"{d.name}: written by {len(makers)} jobs ({', '.join(makers)})")
        for j in self.jobs:
            for x in j.inputs + j.outputs:
                if x not in self._ds:
                    out.append(f"{j.name}: unknown dataset {x}")
        if self._cycle():
            out.append("cycle in the batch: " + " -> ".join(self._cycle()))
        return out

    def _edges(self) -> dict[str, set[str]]:
        """Dataset -> datasets it feeds through one job."""
        e: dict[str, set[str]] = {d: set() for d in self._ds}
        for j in self.jobs:
            for i in j.inputs:
                e.setdefault(i, set()).update(j.outputs)
        return e

    def _cycle(self) -> list[str]:
        e, state, stack = self._edges(), {}, []

        def visit(n):
            state[n] = 1
            stack.append(n)
            for m in sorted(e.get(n, ())):
                if state.get(m) == 1:
                    return stack[stack.index(m):] + [m]
                if m not in state:
                    c = visit(m)
                    if c:
                        return c
            stack.pop()
            state[n] = 2
            return []

        for n in sorted(e):
            if n not in state:
                c = visit(n)
                if c:
                    return c
        return []

    def downstream(self, name: str) -> set[str]:
        e, seen, todo = self._edges(), set(), [name]
        while todo:
            n = todo.pop()
            for m in e.get(n, ()):
                if m not in seen:
                    seen.add(m)
                    todo.append(m)
        return seen

    def upstream(self, name: str) -> set[str]:
        seen, todo = set(), [name]
        while todo:
            j = self.producer(todo.pop())
            if j is None:
                continue
            for i in j.inputs:
                if i not in seen:
                    seen.add(i)
                    todo.append(i)
        return seen

    # ------------------------------------------------------------------ time
    def _order(self) -> list[Job]:
        """Jobs in dependency order (a topological sort; the map must be acyclic)."""
        done, order, left = set(), [], list(self.jobs)
        external = {d.name for d in self.datasets if d.ready is not None}
        while left:
            for j in left:
                if all(i in done or i in external for i in j.inputs):
                    order.append(j)
                    done.update(j.outputs)
                    left.remove(j)
                    break
            else:
                raise ValueError("cycle or missing producer: " + ", ".join(j.name for j in left))
        return order

    def ready_times(self, arrivals: dict | None = None) -> dict[str, float]:
        return self._forward(arrivals)[1]

    def schedule(self, arrivals: dict | None = None) -> dict[str, tuple[float, float]]:
        return self._forward(arrivals)[0]

    def _forward(self, arrivals):
        arrivals = arrivals or {}
        ready = {d.name: arrivals.get(d.name, d.ready) for d in self.datasets
                 if d.ready is not None}
        sched = {}
        for j in self._order():
            deps = max((ready[i] for i in j.inputs), default=0.0)
            start = deps if j.start is None else j.start
            end = start + j.duration
            sched[j.name] = (start, end)
            for o in j.outputs:
                ready[o] = end
        return sched, ready

    def stale_reads(self, arrivals: dict | None = None) -> list[tuple]:
        sched, ready = self._forward(arrivals)
        out = []
        for j in self._order():
            s = sched[j.name][0]
            for i in j.inputs:
                if ready[i] > s + 1e-9:
                    out.append((j.name, i, s, ready[i]))
        return out

    def latest_starts(self, deadline: float) -> dict[str, float]:
        """Backward pass: a job must end by its own deadline (default `deadline`) and
        before the latest start of every job that reads one of its outputs."""
        late: dict[str, float] = {}
        for j in reversed(self._order()):
            end = j.deadline if j.deadline is not None else deadline
            for k in self.jobs:
                if k.name in late and set(j.outputs) & set(k.inputs):
                    end = min(end, late[k.name])
            late[j.name] = end - j.duration
        return late

    def slack(self, deadline: float, arrivals: dict | None = None) -> dict[str, float]:
        late, sched = self.latest_starts(deadline), self.schedule(arrivals)
        return {j: late[j] - sched[j][0] for j in sched}

    def longest_chain(self, arrivals: dict | None = None) -> list[str]:
        sched, ready = self._forward(arrivals)
        j = max(sched, key=lambda n: sched[n][1])
        chain = [j]
        while True:
            job = self._jobs[chain[-1]]
            if job.start is not None or not job.inputs:
                break
            crit = max(job.inputs, key=lambda i: ready[i])
            p = self.producer(crit)
            if p is None:
                break
            chain.append(p.name)
        return chain[::-1]

    def blast_radius(self) -> dict[str, int]:
        return {d.name: len(self.downstream(d.name) & set(self._ds))
                for d in self.datasets if d.ready is not None}
