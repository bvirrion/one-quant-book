"""firm.goldtest -- golden files, test tiers, release trains and deployment checks (Book 15, ch. 27).

A golden file holds reviewed values of a pricer's output with, for each, a tolerance derived from the engine's own
error (a multiple of a Monte Carlo standard error, of a grid's convergence gap, or a relative epsilon for closed
forms) and its provenance (engine, parameters, library version). A new build's values are compared with it; a value
outside its tolerance fails, and the report groups the failures by product so that a change's impact is visible at
once. Updating a golden value is itself a change: it is proposed with the reason and approved by someone else. A tier
runner runs the test tiers in order, timing each and stopping at the first failure. A release-train simulator
follows changes from merge to production under a train cadence. The deployment check refuses a release unless every
host reports the same build and configuration hashes as the release.

API (stable):
    Golden(key, value, tol, provenance) ; GoldenStore(path=None): .put ; .get ; .propose(key, value, tol, reason, by)
        .approve(key, by) (a different person) ; .save() ; .load()
    compare(store, results {key: value}, product_of=None) -> Report(failures [(key, diff, tol)], by_product, n)
    run_tiers([(name, fn)]) -> [(name, seconds, ok)]                  stops after the first failing tier
    release_train(arrivals [day], cadence_days, defect=None) -> TrainStats(lead_days, batch_sizes, bisect_steps)
    host_state(build, config) -> (hash, hash) ; consistency(hosts {host: state}, release_state) -> [host]
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import time
from dataclasses import asdict, dataclass, field


@dataclass
class Golden:
    key: str
    value: float
    tol: float
    provenance: dict = field(default_factory=dict)


class GoldenStore:
    def __init__(self, path: str | pathlib.Path | None = None):
        self.path = pathlib.Path(path) if path else None
        self.items: dict[str, Golden] = {}
        self.pending: dict[str, tuple] = {}

    def put(self, g: Golden) -> None:
        self.items[g.key] = g

    def get(self, key: str) -> Golden:
        return self.items[key]

    def propose(self, key: str, value: float, tol: float, reason: str, by: str) -> None:
        self.pending[key] = (Golden(key, value, tol, {**self.items[key].provenance, "reason": reason}), by)

    def approve(self, key: str, by: str) -> None:
        g, proposer = self.pending[key]
        if by == proposer:
            raise PermissionError("a golden value is approved by someone other than its proposer")
        g.provenance = {**g.provenance, "proposed_by": proposer, "approved_by": by}
        self.items[key] = g
        del self.pending[key]

    def save(self) -> None:
        self.path.write_text(json.dumps({k: asdict(g) for k, g in sorted(self.items.items())}, indent=1))

    def load(self) -> GoldenStore:
        self.items = {k: Golden(**v) for k, v in json.loads(self.path.read_text()).items()}
        return self


@dataclass
class Report:
    failures: list
    by_product: dict
    n: int

    @property
    def ok(self) -> bool:
        return not self.failures


def compare(store: GoldenStore, results: dict, product_of=None) -> Report:
    """Each result against its golden value; a key missing from either side is a failure."""
    product_of = product_of or (lambda k: k.split(":")[0])
    fails, by = [], {}
    for k in sorted(set(store.items) | set(results)):
        if k not in store.items or k not in results:
            fails.append((k, math.inf, 0.0))
        else:
            g = store.items[k]
            diff = results[k] - g.value
            if not abs(diff) <= g.tol:
                fails.append((k, diff, g.tol))
                by[product_of(k)] = by.get(product_of(k), 0) + 1
    return Report(fails, by, len(results))


# ------------------------------------------------------------ tiers, trains, deployments
def run_tiers(tiers) -> list[tuple]:
    out = []
    for name, fn in tiers:
        t0 = time.perf_counter()
        try:
            ok = bool(fn())
        except AssertionError:
            ok = False
        out.append((name, time.perf_counter() - t0, ok))
        if not ok:
            break
    return out


@dataclass
class TrainStats:
    lead_days: list
    batch_sizes: list
    bisect_steps: float


def release_train(arrivals, cadence_days: float) -> TrainStats:
    """Changes merged at `arrivals` (days) leave on the next train, every `cadence_days`
    (0: each change deploys at once). A bad deployment is searched by bisection over its
    batch: ceil(log2(batch)) steps on average per batch that contains the defect."""
    lead, batches = [], {}
    for a in sorted(arrivals):
        dep = a if cadence_days == 0 else math.ceil(a / cadence_days + 1e-12) * cadence_days
        lead.append(dep - a)
        batches[dep] = batches.get(dep, 0) + 1
    sizes = list(batches.values())
    changes = sum(sizes)
    steps = sum(s * math.ceil(math.log2(s)) for s in sizes if s > 1) / changes    # weighted by changes
    return TrainStats(lead, sizes, steps)


def _h(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:12]


def host_state(build: dict, config: dict) -> tuple[str, str]:
    """What a host reports: the hash of the build it runs and of its configuration."""
    return _h(build), _h(config)


def consistency(hosts: dict, release: tuple) -> list[str]:
    """Hosts whose build or configuration differs from the release's: the release is refused
    unless the list is empty."""
    return sorted(h for h, state in hosts.items() if state != release)
