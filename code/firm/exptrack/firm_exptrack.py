"""firm.exptrack -- experiment tracking, a model registry with lineage, and an audit trail (Book 12, chapter 25).

A file-backed tracker: each run is a JSON record of everything that determines its result (parameters, seed, data
snapshot, code version, environment) and everything it produced (metrics, artefacts stored once under their content
hash, Book 7's firm.workflow.content_hash). Run identifiers are hashes of the record, and timestamps are supplied by the
caller, so a tracker's contents are reproducible. Every run is also a trial in Book 7's firm.researchlog, so the trial
count behind a champion and its deflated Sharpe ratio come from the same place. A registry moves models through stages
with their lineage (run, data snapshot, code version); an append-only, hash-chained audit trail records every action.
Standard library and NumPy only.

API (stable):
    Tracker(root, log=None, family=None)
        .run(params, seed, data, code, env, metrics, artefact, ts) -> run id     artefact: any picklable object
        .get(run_id) -> record ; .artefact(hash) -> object ; .runs() -> list of records ; .best(metric) -> record
    Registry(root, audit).register(name, run_id, record, ts) ; .promote(name, version, stage, ts, reason)
        .current(name, stage) -> entry ; .lineage(name, version) -> dict
    AuditTrail(path).append(kind, body, ts) ; .verify() -> index of the first broken link or -1
    reproduce(record, train) -> (artefact hash of the re-run, equal: bool)       train(params, seed, data, code)
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import pickle
import sys

_FIRM = pathlib.Path(__file__).resolve().parents[1]
for _c in ("workflow", "researchlog"):
    sys.path.insert(0, str(_FIRM / _c))
from firm_workflow import content_hash  # noqa: E402

GENESIS = "0" * 64
FIELDS = ("params", "seed", "data", "code", "env")


class AuditTrail:
    """Append-only JSON lines, each carrying the hash of the previous one: editing any line breaks the chain."""

    def __init__(self, path):
        self.path = pathlib.Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch()

    def _lines(self):
        return [json.loads(x) for x in self.path.read_text().splitlines() if x]

    def append(self, kind, body, ts):
        prev = self._lines()[-1]["hash"] if self._lines() else GENESIS
        rec = {"kind": kind, "ts": ts, "body": body, "prev": prev}
        rec["hash"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
        with open(self.path, "a") as f:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
        return rec["hash"]

    def verify(self):
        prev = GENESIS
        for i, rec in enumerate(self._lines()):
            h = rec.pop("hash")
            if rec["prev"] != prev or hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest() != h:
                return i
            prev = h
        return -1


class Tracker:
    def __init__(self, root, log=None, family=None):
        self.root = pathlib.Path(root)
        (self.root / "runs").mkdir(parents=True, exist_ok=True)
        (self.root / "artefacts").mkdir(parents=True, exist_ok=True)
        self.log, self.family = log, family

    def run(self, params, seed, data, code, env, metrics, artefact, ts):
        a_hash = content_hash(pickle.dumps(artefact))
        path = self.root / "artefacts" / a_hash
        if not path.exists():
            path.write_bytes(pickle.dumps(artefact))
        rec = {"params": params, "seed": seed, "data": data, "code": code, "env": env, "metrics": metrics,
               "artefact": a_hash, "ts": ts}
        rid = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()[:16]
        rec["id"] = rid
        (self.root / "runs" / f"{rid}.json").write_text(json.dumps(rec, sort_keys=True))
        if self.log is not None:
            self.log.trial(self.family, params, metrics, ts, code_hash=code, data_id=data)
        return rid

    def get(self, rid):
        return json.loads((self.root / "runs" / f"{rid}.json").read_text())

    def artefact(self, a_hash):
        return pickle.loads((self.root / "artefacts" / a_hash).read_bytes())

    def runs(self):
        return sorted((json.loads(p.read_text()) for p in (self.root / "runs").glob("*.json")), key=lambda r: r["ts"])

    def best(self, metric):
        return max(self.runs(), key=lambda r: r["metrics"][metric])


class Registry:
    """Named models, numbered versions, stages ('candidate', 'production', 'retired'), each version tied to its run."""

    def __init__(self, root, audit):
        self.path = pathlib.Path(root) / "registry.json"
        self.audit = audit
        self.db = json.loads(self.path.read_text()) if self.path.exists() else {}

    def _save(self):
        self.path.write_text(json.dumps(self.db, sort_keys=True))

    def register(self, name, run_id, record, ts):
        versions = self.db.setdefault(name, [])
        entry = {"version": len(versions) + 1, "run": run_id, "artefact": record["artefact"], "data": record["data"],
                 "code": record["code"], "stage": "candidate", "history": [(ts, "candidate", "registered")]}
        versions.append(entry)
        self._save()
        self.audit.append("register", {"name": name, "version": entry["version"], "run": run_id}, ts)
        return entry["version"]

    def promote(self, name, version, stage, ts, reason):
        for e in self.db[name]:
            if stage == "production" and e["stage"] == "production":
                e["stage"] = "retired"
                e["history"].append((ts, "retired", f"replaced by version {version}"))
        e = self.db[name][version - 1]
        e["stage"] = stage
        e["history"].append((ts, stage, reason))
        self._save()
        self.audit.append("promote", {"name": name, "version": version, "stage": stage, "reason": reason}, ts)

    def current(self, name, stage="production"):
        return next((e for e in self.db.get(name, []) if e["stage"] == stage), None)

    def as_of(self, name, ts, stage="production"):
        """The version that was in `stage` at time ts, from the stage histories."""
        best = None
        for e in self.db.get(name, []):
            state = None
            for t, st, _ in e["history"]:
                if t <= ts:
                    state = st
            if state == stage:
                best = e
        return best

    def lineage(self, name, version):
        e = self.db[name][version - 1]
        return {k: e[k] for k in ("run", "artefact", "data", "code")}


def reproduce(record, train):
    """Re-run training from the record's fields alone and compare the artefact's content hash bit for bit."""
    art = train(record["params"], record["seed"], record["data"], record["code"])
    h = content_hash(pickle.dumps(art))
    return h, h == record["artefact"]
