import pathlib
import sys
import tempfile

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "researchlog"))
from firm_researchlog import ResearchLog
from firm_workflow import Pipeline, Stage, content_hash, diff, environment, register, reproduce


def _data(inputs, params, seed):
    x = np.arange(10.0)
    for i, v in params.get("revise", []):
        x[i] = v
    return x


def _clip(inputs, params, seed):
    return np.minimum(inputs["data"], params["cap"])


def _total(inputs, params, seed):
    return float(inputs["clip"].sum())


def _noisy(inputs, params, seed):
    return float(np.random.default_rng(seed).standard_normal())


def make(revise=(), cap=5.0, seed=1):
    def build(cache):
        return Pipeline([Stage("data", _data, (), {"revise": list(revise)}), Stage("clip", _clip, ("data",), {"cap": cap}),
                         Stage("total", _total, ("clip",)), Stage("noise", _noisy, ("total",), {}, seed)], cache)
    return build


def test_hash_is_canonical():
    assert content_hash({"b": 1, "a": np.arange(3)}) == content_hash({"a": np.arange(3), "b": 1})
    assert content_hash(np.arange(3)) != content_hash(np.arange(3.0))              # dtype matters
    assert content_hash([1.0]) != content_hash([1])
    assert set(environment()) == {"python", "numpy", "platform"}


def test_cache_early_cutoff_and_diff():
    with tempfile.TemporaryDirectory() as d:
        out, m1 = make()(d).run()
        assert out["total"] == 0 + 1 + 2 + 3 + 4 + 5 * 5 and all(s["ran"] for s in m1["stages"].values())
        _, m2 = make()(d).run()
        assert not any(s["ran"] for s in m2["stages"].values())                    # everything from the cache
        _, m3 = make(revise=[(8, 20.0)])(d).run()                                  # above the cap: clipped away
        assert [n for n, s in m3["stages"].items() if s["ran"]] == ["data", "clip"]   # early cutoff after clip
        _, m4 = make(revise=[(2, 20.0)])(d).run()
        assert [n for n, s in m4["stages"].items() if s["ran"]] == ["data", "clip", "total", "noise"]
        assert diff(m1, m4) == {"data": ["params", "output"], "clip": ["inputs", "output"], "total": ["inputs", "output"],
                                "noise": ["inputs"]}                          # its output ignores its input
        assert diff(m1, m3) == {"data": ["params", "output"], "clip": ["inputs"]}


def test_reproduce_and_register():
    with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as e, tempfile.TemporaryDirectory() as f:
        _, m = make()(d).run()
        assert reproduce(make(), m, e) == []                                        # bit for bit
        _, u = make(seed=None)(d).run()
        assert reproduce(make(seed=None), u, f) == ["noise"]                        # no seed, no reproduction
        log = ResearchLog()
        log.register("clip", "clipping helps", "2026-09-25T09:00:00")
        entry = register(m, log, "clip", "2026-09-25T10:00:00", {"total": 35.0}, data_stage="data")
        assert log.trial_count("clip") == 1 and entry.body["data_id"] == m["stages"]["data"]["output"]
