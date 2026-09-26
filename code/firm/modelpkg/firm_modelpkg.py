"""firm.modelpkg -- the handoff specification between research and production, its validator, and a simulator of the
research-to-production pipeline (Book 12, chapter 28).

A handoff package is a JSON manifest beside the files it names: the model artefact and its content hash (Book 7's
firm.workflow), the feature specification as firm.featstore definitions, test vectors with the outputs the model must
reproduce and a tolerance, a latency budget and the measured latency, the monitoring specification (firm.mlmonitor's
statistics, thresholds, false-page rate, owner) and the model card (firm.modelcard). validate() runs every check a
continuous-integration job would: schema, hash, features (known inputs and aggregations, unique names, as many as the
model reads, and offline-online parity on a sample of events), test vectors through firm.mlinfer's forest kernel,
latency, monitoring and card. The pipeline simulator is a network of queues: models arrive, wait for a team, are
served, and at each gate are passed, sent back for rework or killed; it measures lead times and where models die.

API (stable):
    REQUIRED ; INPUTS ; MONITORS
    load(path) -> manifest dict (paths resolved against the manifest's directory)
    validate(pkg, events=None, times=None) -> list of (check, passed, detail); with events, also offline-online parity
        and, when the package names feature_vectors (a CSV of research's values at those times), feature vectors
    Station(name, servers, mean, kill, rework, rework_to, dist) ; simulate_pipeline(stations, rate, n, seed)
        -> dict of arrays: arrival, done (inf if killed), exit (production or kill time), killed_at (station index or
           -1), visits (models x stations)
"""
from __future__ import annotations

import heapq
import json
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

_FIRM = pathlib.Path(__file__).resolve().parents[1]
for _c in ("workflow", "featstore", "mlinfer", "modelcard"):
    sys.path.insert(0, str(_FIRM / _c))
from firm_featstore import FeatureDef, offline, parity, stream  # noqa: E402
from firm_mlinfer import forest_predict, read_forest  # noqa: E402
from firm_modelcard import ModelCard  # noqa: E402
from firm_workflow import content_hash  # noqa: E402

REQUIRED = ("name", "version", "artefact", "artefact_hash", "features", "test_vectors", "tolerance",
            "latency_budget_us", "latency_measured_us", "monitoring", "card")
INPUTS = ("t", "mid", "spread", "imbalance", "depth", "wmid", "ofi", "trade_qty", "trade_sign", "is_trade", "one")
AGGS = ("last", "sum", "count", "change")
MONITORS = ("feature psi", "feature ks", "prediction psi", "inside threshold", "ic cusum")


def load(path):
    path = pathlib.Path(path)
    pkg = json.loads(path.read_text())
    for k in ("artefact", "test_vectors", "feature_vectors"):
        if k in pkg:
            pkg[k] = str(path.parent / pkg[k])
    return pkg


def _features(pkg):
    return [FeatureDef(**f) for f in pkg["features"]]


def validate(pkg, events=None, times=None):
    """Every check, in order; a check that cannot run because an earlier one failed is reported as failed."""
    out = []
    missing = [k for k in REQUIRED if k not in pkg]
    out.append(("schema", not missing, f"missing: {missing}" if missing else "all fields present"))
    if missing:
        return out
    raw = pathlib.Path(pkg["artefact"]).read_bytes()
    ok = content_hash(raw) == pkg["artefact_hash"]
    out.append(("artefact hash", ok, "matches" if ok else "the artefact is not the one the hash names"))
    forest = read_forest(pkg["artefact"])
    n_in = int(forest["feature"].max()) + 1
    try:
        defs = _features(pkg)
    except TypeError as e:
        defs, err = [], str(e)
    else:
        err = ""
    bad = [d.name for d in defs if d.input not in INPUTS or d.agg not in AGGS or d.window < 0]
    names = [d.name for d in defs]
    ok = not err and not bad and len(set(names)) == len(names) and len(defs) == n_in
    detail = err or (f"unknown input or aggregation: {bad}" if bad else
                     f"{len(defs)} features for a model reading {n_in}" if len(defs) != n_in else
                     "duplicate names" if len(set(names)) != len(names) else f"{len(defs)} features")
    out.append(("feature specification", ok, detail))
    if events is not None and ok:
        off = offline(events, defs, times)
        p = parity(off, stream(events, defs, times))
        out.append(("feature parity", p["mismatch share"] == 0, f"mismatch share {p['mismatch share']:.3f}"))
        if pkg.get("feature_vectors") is not None:
            want = np.loadtxt(pkg["feature_vectors"], delimiter=",", ndmin=2)
            e = float(np.max(np.abs(off - want)))
            out.append(("feature vectors", e <= 1e-9, f"largest error {e:.3g} against research's values"))
    V = np.loadtxt(pkg["test_vectors"], delimiter=",", ndmin=2)
    got, want = forest_predict(forest, V[:, :n_in]), V[:, n_in]
    err = float(np.max(np.abs(got - want)))
    out.append(("test vectors", err <= pkg["tolerance"], f"{len(V)} vectors, largest error {err:.3g}"))
    ok = 0 < pkg["latency_measured_us"] <= pkg["latency_budget_us"]
    out.append(("latency", ok, f"{pkg['latency_measured_us']} us measured, budget {pkg['latency_budget_us']} us"))
    mons = pkg["monitoring"]
    bad = [m.get("statistic") for m in mons if m.get("statistic") not in MONITORS
           or not all(k in m for k in ("threshold", "pages_per_month", "owner"))]
    out.append(("monitoring", bool(mons) and not bad, f"incomplete: {bad}" if bad else f"{len(mons)} monitors"))
    miss = ModelCard(pkg["card"]).missing()
    out.append(("model card", not miss, f"missing: {miss}" if miss else "complete"))
    return out


# ---------------------------------------------------------------------------------------------------- pipeline
@dataclass(frozen=True)
class Station:
    """A team: `servers` people working one model each, service times of mean `mean` weeks ('exp' or 'fixed'); after
    service a model is killed with probability kill, sent back to station rework_to with probability rework, or
    passed on (to next_to, or the next station). servers = 0 means no queue (as many in parallel as arrive). Stations
    whose name starts with '~' are side loops (rework), reached only through rework_to and left through next_to; the
    main line ends at the last station before them."""
    name: str
    servers: int
    mean: float
    kill: float = 0.0
    rework: float = 0.0
    rework_to: int = -1
    dist: str = "exp"
    next_to: int = -1                                              # where a passed model goes; -1: the next station


def simulate_pipeline(stations, rate, n, seed=0):
    """Event-driven simulation of n models arriving as a Poisson stream (rate per week) through the stations in
    order, first come first served at each."""
    rng = np.random.default_rng(seed)
    arrival = np.cumsum(rng.exponential(1 / rate, n))
    done, killed, visits = np.full(n, np.inf), np.full(n, -1), np.zeros((n, len(stations)), dtype=int)
    exit_t = np.full(n, np.inf)
    free = [s.servers for s in stations]
    queues = [[] for _ in stations]
    ev = [(arrival[i], 0, i, 0) for i in range(n)]                    # (time, kind 0 arrive / 1 finish, model, station)
    heapq.heapify(ev)

    def start(t, i, k):
        s = stations[k]
        dur = s.mean if s.dist == "fixed" else rng.exponential(s.mean)
        heapq.heappush(ev, (t + dur, 1, i, k))

    while ev:
        t, kind, i, k = heapq.heappop(ev)
        if kind == 0:
            visits[i, k] += 1
            if stations[k].servers == 0:
                start(t, i, k)
            elif free[k] > 0:
                free[k] -= 1
                start(t, i, k)
            else:
                queues[k].append(i)
            continue
        if stations[k].servers > 0:
            if queues[k]:
                start(t, queues[k].pop(0), k)
            else:
                free[k] += 1
        s, u = stations[k], rng.random()
        if u < s.kill:
            killed[i], exit_t[i] = k, t
        elif u < s.kill + s.rework:
            heapq.heappush(ev, (t, 0, i, s.rework_to))
        elif s.next_to >= 0:
            heapq.heappush(ev, (t, 0, i, s.next_to))
        elif k + 1 < len(stations) and not stations[k + 1].name.startswith("~"):
            heapq.heappush(ev, (t, 0, i, k + 1))
        else:
            done[i] = exit_t[i] = t
    return {"arrival": arrival, "done": done, "exit": exit_t, "killed_at": killed, "visits": visits}
