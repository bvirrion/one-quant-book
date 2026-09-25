"""firm.workflow -- the research pipeline (build of One Quant Book 7, chapter 29).

A pipeline is a directed acyclic graph of stages. Each stage is a function of its dependencies' outputs, its
parameters and its seed. Its key is the SHA-256 of its name, the hash of its source code, its canonical parameters,
its seed and the content hashes of its dependencies' outputs; its output is stored under that key in a
content-addressed cache and hashed in turn. A stage whose key is in the cache is not run. Because keys are built from
the dependencies' output hashes (not their keys), a change upstream that leaves an intermediate output unchanged
stops there (early cutoff). A run writes a manifest: every stage's key, code hash, parameters, seed, dependencies,
output hash and whether it ran, and the environment. Reproduction re-runs every stage in an empty cache and compares
output hashes bit for bit; the diff of two manifests says which stages changed and why; a run is registered as a
trial in firm.researchlog. Standard library and NumPy only.

API (stable):
    content_hash(obj)                    SHA-256 of a canonical encoding (arrays by dtype, shape, bytes; dicts sorted)
    Stage(name, fn, deps, params, seed)  fn(inputs: dict, params: dict, seed) -> output
    Pipeline(stages, cache_dir)          .run(target=None) -> (outputs, manifest); .keys after a run
    environment()                        {'python', 'numpy', 'platform'}
    reproduce(make_pipeline, manifest, cache_dir)   [stage names whose output hash differs when re-run from scratch]
    diff(m1, m2)                         {stage: [reasons]} over 'code', 'params', 'seed', 'inputs', 'output'
    register(manifest, log, family, ts, metrics)    a researchlog trial with the manifest's hash and data key
"""
from __future__ import annotations

import hashlib
import inspect
import json
import pathlib
import pickle
import platform
import sys
from dataclasses import dataclass, field

import numpy as np


def _encode(obj, h):
    if isinstance(obj, np.ndarray):
        a = np.ascontiguousarray(obj)
        h.update(b"nd" + str(a.dtype).encode() + str(a.shape).encode())
        h.update(a.tobytes() if a.dtype != object else pickle.dumps(a.tolist(), protocol=4))
    elif isinstance(obj, dict):
        h.update(b"{")
        for k in sorted(obj, key=str):
            _encode(str(k), h)
            _encode(obj[k], h)
        h.update(b"}")
    elif isinstance(obj, (list, tuple)):
        h.update(b"[" if isinstance(obj, list) else b"(")
        for x in obj:
            _encode(x, h)
        h.update(b"]")
    elif isinstance(obj, (np.floating, float)):
        h.update(b"f" + np.float64(obj).tobytes())
    elif isinstance(obj, (np.integer, int, bool)):
        h.update(b"i" + str(int(obj)).encode())
    elif obj is None:
        h.update(b"N")
    elif isinstance(obj, str):
        h.update(b"s" + obj.encode())
    else:
        h.update(b"p" + pickle.dumps(obj, protocol=4))


def content_hash(obj) -> str:
    h = hashlib.sha256()
    _encode(obj, h)
    return h.hexdigest()


@dataclass
class Stage:
    name: str
    fn: object
    deps: tuple = ()
    params: dict = field(default_factory=dict)
    seed: int | None = None

    def code_hash(self) -> str:
        return hashlib.sha256(inspect.getsource(self.fn).encode()).hexdigest()


def environment() -> dict:
    return {"python": sys.version.split()[0], "numpy": np.__version__, "platform": platform.platform()}


class Pipeline:
    def __init__(self, stages, cache_dir):
        self.stages = {s.name: s for s in stages}
        self.cache = pathlib.Path(cache_dir)
        self.cache.mkdir(parents=True, exist_ok=True)
        self.keys = {}

    def _order(self, target):
        seen, order = set(), []

        def visit(n):
            if n in seen:
                return
            for d in self.stages[n].deps:
                visit(d)
            seen.add(n)
            order.append(n)
        for n in ([target] if target else self.stages):
            visit(n)
        return order

    def run(self, target=None):
        outputs, out_hash, manifest = {}, {}, {"stages": {}, "env": environment()}
        for n in self._order(target):
            s = self.stages[n]
            code = s.code_hash()
            key = content_hash([n, code, s.params, s.seed, [out_hash[d] for d in s.deps]])
            path = self.cache / f"{key}.pkl"
            ran = not path.exists()
            if ran:
                out = s.fn({d: outputs[d] for d in s.deps}, s.params, s.seed)
                path.write_bytes(pickle.dumps(out, protocol=4))
            else:
                out = pickle.loads(path.read_bytes())
            outputs[n], out_hash[n], self.keys[n] = out, content_hash(out), key
            manifest["stages"][n] = {"key": key, "code": code, "params": s.params, "seed": s.seed, "deps": list(s.deps),
                                     "inputs": [out_hash[d] for d in s.deps], "output": out_hash[n], "ran": ran}
        return outputs, manifest


def reproduce(make_pipeline, manifest: dict, cache_dir) -> list:
    """Re-run the pipeline built by make_pipeline() in an empty cache_dir; the stages whose outputs differ."""
    _, again = make_pipeline(cache_dir).run()
    return [n for n, m in manifest["stages"].items() if again["stages"][n]["output"] != m["output"]]


def diff(m1: dict, m2: dict) -> dict:
    out = {}
    for n in m1["stages"]:
        a, b = m1["stages"][n], m2["stages"].get(n)
        if b is None:
            out[n] = ["removed"]
            continue
        r = [k for k in ("code", "params", "seed", "inputs", "output") if content_hash(a[k]) != content_hash(b[k])]
        if r:
            out[n] = r
    return out


def register(manifest: dict, log, family: str, ts: str, metrics: dict, data_stage: str = "snapshot"):
    body = json.dumps({n: m["key"] for n, m in manifest["stages"].items()}, sort_keys=True)
    return log.trial(family, {"stages": len(manifest["stages"])}, metrics, ts,
                     code_hash=hashlib.sha256(body.encode()).hexdigest(),
                     data_id=manifest["stages"].get(data_stage, {}).get("output", ""))
