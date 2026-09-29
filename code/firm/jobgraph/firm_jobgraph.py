"""firm.jobgraph -- task graphs, schedulers and a discrete-event cluster (build of One Quant Book 15, chapter 13).

A sweep is a task graph: each task has a true duration (unknown to the scheduler), an estimate (known), a team, a
number of cores, dependencies and an optional cache key. A cluster is a set of nodes with cores and a speed each
(a slow node runs every task `slowdown` times longer), failure and preemption rates per core-hour, and a price per
node-hour. The simulator runs a task graph on a cluster under a scheduling policy and returns the schedule, its
makespan and its cost. Policies:
    FIFO         submission order
    LPT          longest estimate first (Graham's longest-processing-time list scheduling)
    FairShare    between teams: the next task comes from the team using the smallest share of its target
    WorkStealing each core owns a deque (tasks dealt round robin); an idle core steals from the far end of the fullest
Speculative execution gives a task that has run `spec` times its estimate one backup copy, on another node, on
the next free core (before the queue); the first copy to finish wins and the other is killed. A task whose cache key
is already in the cache takes no time.

API (stable):
    Task(tid, duration, estimate, team='A', cores=1, deps=(), key=None, release=0.0)
    Cluster(nodes, cores, slow=(), slowdown=1.0, fail_per_hour=0.0, preempt_per_hour=0.0, price=1.0, seed=0)
    simulate(tasks, cluster, policy, spec=None, cache=None) -> Schedule
    Schedule: runs [(tid, core, start, end, outcome)], finish {tid: t}, makespan, busy (core-seconds),
              node_hours (nodes x makespan), wasted (core-seconds of failed, preempted and killed attempts), backups
    lower_bound(tasks, total_cores) -> max(total work / cores, longest task, longest dependency chain)
    utilisation(schedule, grid) -> busy cores at each grid time
    LocalExecutor(policy).run(tasks, fns) -> [(tid, start, end)]   one worker, real callables, in the policy's order
"""
from __future__ import annotations

import heapq
import random
import time
from collections import deque
from dataclasses import dataclass, field


@dataclass
class Task:
    tid: int
    duration: float                 # true seconds on a normal node (the scheduler does not see it)
    estimate: float                 # what the scheduler sees
    team: str = "A"
    cores: int = 1
    deps: tuple = ()
    key: str | None = None
    release: float = 0.0            # submission time


@dataclass
class Cluster:
    nodes: int
    cores: int                      # per node
    slow: tuple = ()                # indices of slow nodes
    slowdown: float = 1.0
    fail_per_hour: float = 0.0      # per core-hour of running work
    preempt_per_hour: float = 0.0
    price: float = 1.0              # per node-hour
    seed: int = 0

    @property
    def total(self) -> int:
        return self.nodes * self.cores

    def speed(self, core: int) -> float:
        return self.slowdown if core // self.cores in self.slow else 1.0


@dataclass
class Schedule:
    runs: list = field(default_factory=list)
    finish: dict = field(default_factory=dict)
    makespan: float = 0.0
    busy: float = 0.0
    wasted: float = 0.0
    backups: int = 0
    node_hours: float = 0.0
    cost: float = 0.0


# ------------------------------------------------------------ policies
class FIFO:
    def __init__(self):
        self.q: deque = deque()

    def push(self, task: Task, front: bool = False) -> None:
        (self.q.appendleft if front else self.q.append)(task)

    def pop(self, core: int, running: dict):
        return self.q.popleft() if self.q else None

    def __len__(self) -> int:
        return len(self.q)


class LPT(FIFO):
    def __init__(self):
        self.h: list = []
        self.n = 0

    def push(self, task: Task, front: bool = False) -> None:
        heapq.heappush(self.h, (-task.estimate, self.n, task))
        self.n += 1

    def pop(self, core: int, running: dict):
        return heapq.heappop(self.h)[2] if self.h else None

    def __len__(self) -> int:
        return len(self.h)


class FairShare(FIFO):
    """Per-team queues; next task from the team using fewest cores per unit of target."""

    def __init__(self, targets: dict):
        self.targets, self.qs = targets, {t: deque() for t in targets}

    def push(self, task: Task, front: bool = False) -> None:
        (self.qs[task.team].appendleft if front else self.qs[task.team].append)(task)

    def pop(self, core: int, running: dict):
        use = {t: 0 for t in self.targets}
        for task in running.values():
            use[task.team] += task.cores
        ready = [t for t in self.targets if self.qs[t]]
        if not ready:
            return None
        team = min(ready, key=lambda t: (use[t] / self.targets[t], t))
        return self.qs[team].popleft()

    def __len__(self) -> int:
        return sum(len(q) for q in self.qs.values())


class WorkStealing(FIFO):
    """Tasks dealt round robin to per-core deques; a core takes its head or steals a tail."""

    def __init__(self, cores: int):
        self.dq = [deque() for _ in range(cores)]
        self.i = 0
        self.steals = 0

    def push(self, task: Task, front: bool = False) -> None:
        self.dq[self.i % len(self.dq)].append(task)
        self.i += 1

    def pop(self, core: int, running: dict):
        if self.dq[core]:
            return self.dq[core].popleft()
        victim = max(range(len(self.dq)), key=lambda c: len(self.dq[c]))
        if self.dq[victim]:
            self.steals += 1
            return self.dq[victim].pop()
        return None

    def __len__(self) -> int:
        return sum(len(d) for d in self.dq)


# ------------------------------------------------------------ the simulator
def simulate(tasks: list[Task], cluster: Cluster, policy, spec: float | None = None,
             cache: set | None = None) -> Schedule:
    rng = random.Random(cluster.seed)
    by_id = {t.tid: t for t in tasks}
    waiting = {t.tid: set(t.deps) for t in tasks}
    children: dict = {}
    for t in tasks:
        for d in t.deps:
            children.setdefault(d, []).append(t.tid)
    sched, now, seq = Schedule(), 0.0, 0
    free = list(range(cluster.total))
    running: dict = {}                    # core -> task
    attempt: dict = {}                    # core -> (start, attempt id)
    copies: dict = {}                     # tid -> set of cores running it
    events: list = []
    done: set = set()
    rate = (cluster.fail_per_hour + cluster.preempt_per_hour) / 3600.0

    def push_event(t, kind, core, aid):
        nonlocal seq
        heapq.heappush(events, (t, seq, kind, core, aid))
        seq += 1

    def start(core, task, backup=False):
        nonlocal seq
        running[core] = task
        dur = 0.0 if (cache is not None and task.key in cache) else task.duration * cluster.speed(core)
        aid = seq
        attempt[core] = (now, aid)
        copies.setdefault(task.tid, set()).add(core)
        t_fail = now + rng.expovariate(rate) if rate > 0 else float("inf")
        if t_fail < now + dur:
            share = cluster.fail_per_hour / (cluster.fail_per_hour + cluster.preempt_per_hour)
            kind = "fail" if rng.random() < share else "preempt"
            push_event(t_fail, kind, core, aid)
        else:
            push_event(now + dur, "done", core, aid)
        if spec is not None and not backup and dur > 0:
            push_event(now + spec * task.estimate, "check", core, aid)
        if backup:
            sched.backups += 1

    for t in tasks:
        if not t.deps and t.release <= 0:
            policy.push(t)
        elif not t.deps:
            push_event(t.release, "release", -1, t.tid)

    late: list = []                       # (core, attempt) of tasks waiting for a backup copy

    def fill():
        free.sort()
        while late and free:                  # a late task's backup goes before the queue
            core, aid = late.pop(0)
            if attempt.get(core, (0, None))[1] != aid or len(copies[running[core].tid]) != 1:
                continue
            node = core // cluster.cores
            other = next((c for c in free if c // cluster.cores != node), None)
            if other is None:
                late.insert(0, (core, aid))
                break
            free.remove(other)
            start(other, running[core], backup=True)
        while free and len(policy):
            core = free[0]
            task = policy.pop(core, running)
            if task is None:
                break
            free.pop(0)
            start(core, task)

    fill()
    while events:
        now, _, kind, core, aid = heapq.heappop(events)
        if kind == "release":
            policy.push(by_id[aid])
            fill()
            continue
        if core not in attempt or attempt[core][1] != aid:
            continue                                   # a killed copy's stale event
        task = running[core]
        t0 = attempt[core][0]
        if kind == "check":                    # still running at `spec` times its estimate
            late.append((core, aid))
            fill()
            continue
        del running[core], attempt[core]
        copies[task.tid].discard(core)
        sched.busy += now - t0
        free.append(core)
        if kind in ("fail", "preempt"):
            sched.runs.append((task.tid, core, t0, now, kind))
            sched.wasted += now - t0
            if not copies[task.tid]:
                policy.push(task, front=True)          # retried first
        else:
            sched.runs.append((task.tid, core, t0, now, "done"))
            for c in list(copies[task.tid]):           # kill the other copy
                s0 = attempt[c][0]
                sched.busy += now - s0
                sched.wasted += now - s0
                sched.runs.append((task.tid, c, s0, now, "killed"))
                del running[c], attempt[c]
                free.append(c)
            copies[task.tid] = set()
            if task.tid not in done:
                done.add(task.tid)
                sched.finish[task.tid] = now
                if cache is not None and task.key is not None:
                    cache.add(task.key)
                for ch in children.get(task.tid, ()):
                    waiting[ch].discard(task.tid)
                    if not waiting[ch]:
                        policy.push(by_id[ch])
        fill()
    sched.makespan = max(sched.finish.values(), default=0.0)
    sched.node_hours = cluster.nodes * sched.makespan / 3600.0
    sched.cost = sched.node_hours * cluster.price
    return sched


def lower_bound(tasks: list[Task], total_cores: int) -> float:
    """No schedule beats the work over every core, the longest task, or the longest chain."""
    by_id = {t.tid: t for t in tasks}
    memo: dict = {}

    def chain(tid):
        if tid not in memo:
            t = by_id[tid]
            memo[tid] = t.duration + max((chain(d) for d in t.deps), default=0.0)
        return memo[tid]

    work = sum(t.duration * t.cores for t in tasks)
    longest = max(t.duration for t in tasks)
    return max(work / total_cores, longest, max(chain(t.tid) for t in tasks))


def utilisation(s: Schedule, grid) -> list[int]:
    out = []
    for g in grid:
        out.append(sum(1 for _tid, _c, a, b, _o in s.runs if a <= g < b))
    return out


class LocalExecutor:
    """One worker on this machine: real callables run in the order the policy gives them."""

    def __init__(self, policy):
        self.policy = policy

    def run(self, tasks: list[Task], fns: dict) -> list[tuple]:
        for t in tasks:
            self.policy.push(t)
        out = []
        while len(self.policy):
            t = self.policy.pop(0, {})
            a = time.perf_counter()
            fns[t.tid]()
            out.append((t.tid, a, time.perf_counter()))
        return out
