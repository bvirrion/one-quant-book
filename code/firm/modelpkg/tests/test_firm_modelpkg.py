"""Acceptance tests for firm.modelpkg (Book 12, chapter 28)."""
import copy
import json
import pathlib
import sys

import numpy as np

_FIRM = pathlib.Path(__file__).resolve().parents[2]
for _c in ("modelpkg", "workflow", "modelcard"):
    sys.path.insert(0, str(_FIRM / _c))
import firm_modelpkg as mp  # noqa: E402
from firm_modelcard import CARD_FIELDS  # noqa: E402
from firm_workflow import content_hash  # noqa: E402

DATA = _FIRM / "mlinfer" / "data"


def package(tmp_path):
    art = DATA / "forest.txt"
    feats = [{"name": f"f{j}", "input": "ofi", "agg": "sum", "window": float(j + 1)} for j in range(16)]
    pkg = {"name": "m", "version": 1, "artefact": str(art), "artefact_hash": content_hash(art.read_bytes()),
           "features": feats, "test_vectors": str(DATA / "vectors.csv"), "tolerance": 1e-12,
           "latency_budget_us": 5.0, "latency_measured_us": 2.0,
           "monitoring": [{"statistic": "ic cusum", "threshold": 0.1, "pages_per_month": 1, "owner": "a"}],
           "card": {f: "x" for f in CARD_FIELDS}}
    (tmp_path / "manifest.json").write_text(json.dumps(pkg))
    return mp.load(tmp_path / "manifest.json")


def failing(pkg):
    return [c for c, ok, _ in mp.validate(pkg) if not ok]


def test_complete_package_passes_and_defects_fail(tmp_path):
    pkg = package(tmp_path)
    assert failing(pkg) == [] and len(mp.validate(pkg)) == 7
    p = copy.deepcopy(pkg)
    del p["card"]
    assert failing(p) == ["schema"]
    p = copy.deepcopy(pkg)
    p["artefact_hash"] = "0" * 64
    assert failing(p) == ["artefact hash"]
    p = copy.deepcopy(pkg)
    p["features"][0]["input"] = "microprice"
    assert failing(p) == ["feature specification"]
    p = copy.deepcopy(pkg)
    V = np.loadtxt(p["test_vectors"], delimiter=",")
    V[0, 16] += 1e-6
    np.savetxt(tmp_path / "v.csv", V, delimiter=",", fmt="%.17g")
    p["test_vectors"] = str(tmp_path / "v.csv")
    assert failing(p) == ["test vectors"]


def test_mm1_station_matches_theory():
    r = mp.simulate_pipeline((mp.Station("one", 1, 1.0),), 0.8, 100_000, seed=3)
    w = np.mean((r["done"] - r["arrival"])[1000:])
    assert abs(w - 5.0) < 0.3 and np.array_equal(r["done"], r["exit"])


def test_delay_line_and_routing():
    r = mp.simulate_pipeline((mp.Station("wait", 0, 4.0, dist="fixed"),), 1.0, 100, seed=0)
    assert np.allclose(r["done"] - r["arrival"], 4.0)
    st = (mp.Station("gate", 0, 1.0, kill=0.3, rework=0.2, rework_to=1, dist="fixed"),
          mp.Station("~fix", 0, 1.0, next_to=0, dist="fixed"))
    r = mp.simulate_pipeline(st, 1.0, 20_000, seed=1)
    reach = np.isfinite(r["done"]).mean()
    assert abs(reach - 0.5 / 0.8) < 0.02                                 # pass 0.5 per visit, leave 0.8 per visit
    assert abs(r["visits"][:, 0].mean() - 1 / 0.8) < 0.02
    assert set(np.unique(r["killed_at"])) == {-1, 0} and np.all(np.isfinite(r["exit"]))
