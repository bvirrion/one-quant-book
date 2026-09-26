import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_exptrack import AuditTrail, Registry, Tracker, reproduce  # noqa: E402


def _train(params, seed, data, code):
    return {"w": [params["a"] * seed, len(data), code]}


def _rec(tr, a, seed, ts):
    return tr.get(tr.run({"a": a}, seed, "snap-1", "v1", {}, {"m": a * seed}, _train({"a": a}, seed, "snap-1", "v1"), ts))


def test_tracker_and_reproduction(tmp_path):
    tr = Tracker(tmp_path / "t")
    r1, r2 = _rec(tr, 2, 3, "2026-01-01"), _rec(tr, 2, 3, "2026-01-02")
    assert r1["artefact"] == r2["artefact"] and r1["id"] != r2["id"]
    assert len(list((tmp_path / "t" / "artefacts").iterdir())) == 1
    assert reproduce(r1, _train)[1] and not reproduce(dict(r1) | {"seed": 4}, _train)[1]
    assert tr.best("m")["id"] in (r1["id"], r2["id"])


def test_registry_as_of_and_retirement(tmp_path):
    tr = Tracker(tmp_path / "t")
    audit = AuditTrail(tmp_path / "audit.jsonl")
    reg = Registry(tmp_path, audit)
    a, b = _rec(tr, 1, 1, "2026-01-01"), _rec(tr, 2, 1, "2026-01-02")
    v1 = reg.register("m", a["id"], a, "2026-01-03")
    reg.promote("m", v1, "production", "2026-01-05", "first")
    v2 = reg.register("m", b["id"], b, "2026-02-01")
    reg.promote("m", v2, "production", "2026-02-10", "better")
    assert reg.as_of("m", "2026-01-20")["version"] == 1 and reg.as_of("m", "2026-02-15")["version"] == 2
    assert reg.db["m"][0]["stage"] == "retired" and reg.lineage("m", 2)["run"] == b["id"]
    assert audit.verify() == -1


def test_tampering_detected(tmp_path):
    audit = AuditTrail(tmp_path / "a.jsonl")
    for i in range(5):
        audit.append("x", {"i": i}, f"t{i}")
    lines = (tmp_path / "a.jsonl").read_text().splitlines()
    rec = json.loads(lines[2])
    rec["body"]["i"] = 99
    lines[2] = json.dumps(rec, sort_keys=True)
    (tmp_path / "a.jsonl").write_text("\n".join(lines) + "\n")
    assert audit.verify() == 2
