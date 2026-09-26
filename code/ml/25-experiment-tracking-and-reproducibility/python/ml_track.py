"""Experiment tracking and reproducibility (One Quant Book 12, chapter 25).

Two hundred tuning runs of a gradient-boosted cross-sectional forecast (firm.gbdt) on a synthetic panel, tracked in a
file-backed tracker (firm.exptrack) and logged as trials in firm.researchlog; the champion by validation Sharpe ratio is
registered, promoted, and reproduced bit for bit from the registry alone. Then each field of its record is replaced by
what a team would assume if it had not been recorded (default parameters, default seed, the latest data snapshot, the
current feature code) and the reproduction is tried again."""
from __future__ import annotations

import functools
import math
import os
import pathlib
import sys
import tempfile

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402

_FIRM = pathlib.Path(__file__).resolve().parents[3] / "firm"
for _c in ("exptrack", "gbdt", "researchlog", "multitest"):
    sys.path.insert(0, str(_FIRM / _c))
from firm_exptrack import FIELDS, AuditTrail, Registry, Tracker, reproduce  # noqa: E402
from firm_gbdt import DEFAULTS, make, to_dict  # noqa: E402
from firm_researchlog import ResearchLog  # noqa: E402

DAYS, NAMES, K = 700, 40, 8
TRAIN, VALID = 400, 150
N_RUNS = 200
ENV = {"python": "3.10", "lightgbm threads": 1, "deterministic": True}


@functools.lru_cache(maxsize=2)
def data(snapshot="2026-01"):
    """Features and next-day returns; the March snapshot corrects 1% of the returns (a vendor revision)."""
    rng = np.random.default_rng(0)
    X = rng.standard_normal((DAYS, NAMES, K))
    beta = np.r_[0.005, -0.004, 0.003, np.zeros(K - 3)]
    y = X @ beta * 0.01 + 0.01 * rng.standard_t(4, (DAYS, NAMES)) / math.sqrt(2)
    y += 0.001 * np.tanh(X[:, :, 3] * X[:, :, 4])
    if snapshot == "2026-03":
        fix = np.random.default_rng(1).random((DAYS, NAMES)) < 0.01
        y = np.where(fix, y + 0.01 * np.random.default_rng(2).standard_normal((DAYS, NAMES)), y)
    return X, y


def features(X, code):
    """Feature code: v1 clips at 3 standard deviations, v2 (the current version) at 2.5."""
    return np.clip(X, -3.0, 3.0) if code == "v1" else np.clip(X, -2.5, 2.5)


def fit(params, seed, snapshot, code):
    X, y = data(snapshot)
    return make(params, seed=seed).fit(features(X, code)[:TRAIN].reshape(-1, K), y[:TRAIN].ravel())


def train(params, seed, snapshot, code):
    """The artefact is the fitted model's dump (every tree), whose content hash identifies it bit for bit."""
    return to_dict(fit(params, seed, snapshot, code))


def sharpe(model, snapshot, code, days):
    """Annualised Sharpe ratio of the daily long-short portfolio on the forecast's sign against its median."""
    X, y = data(snapshot)
    days = np.asarray(list(days))
    P = model.predict(features(X, code)[days].reshape(-1, K)).reshape(len(days), NAMES)
    w = np.sign(P - np.median(P, axis=1, keepdims=True))
    pnl = (w * y[days]).sum(1) / NAMES
    return float(pnl.mean() / pnl.std() * math.sqrt(252)), pnl


GRID = {"num_leaves": (7, 15, 31), "learning_rate": (0.01, 0.03, 0.1), "n_estimators": (100, 200),
        "min_child_samples": (50, 100, 200), "colsample_bytree": (0.6, 0.8, 1.0)}


@functools.lru_cache(maxsize=1)
def study():
    root = pathlib.Path(tempfile.mkdtemp(prefix="oqb12_ch25_"))
    log = ResearchLog(root / "research.jsonl")
    log.register("gbdt tuning", "boosted trees beat the linear forecast on the validation block", "2026-02-01T09:00")
    tr = Tracker(root / "tracker", log, "gbdt tuning")
    rng = np.random.default_rng(7)
    valid = range(TRAIN, TRAIN + VALID)
    for i in range(N_RUNS):
        params = dict(DEFAULTS) | {k: v[rng.integers(len(v))] for k, v in GRID.items()}
        params = {k: (float(v) if isinstance(v, float) else int(v) if isinstance(v, (int, np.integer)) else v)
                  for k, v in params.items()}
        seed = int(rng.integers(1, 1000))
        m = fit(params, seed, "2026-01", "v1")
        sr, _ = sharpe(m, "2026-01", "v1", valid)
        tr.run(params, seed, "2026-01", "v1", ENV, {"valid sharpe": sr}, to_dict(m),
               f"2026-02-{1 + i // 20:02d}T{i % 20:02d}:00")
    audit = AuditTrail(root / "audit.jsonl")
    reg = Registry(root, audit)
    champ = tr.best("valid sharpe")
    v = reg.register("xs-gbdt", champ["id"], champ, "2026-02-27T10:00")
    reg.promote("xs-gbdt", v, "production", "2026-03-02T07:00", "champion of 200 runs; validation Sharpe ratio")
    return {"root": root, "tracker": tr, "log": log, "registry": reg, "audit": audit, "champion": champ}


def summary():
    s = study()
    vals = np.array([r["metrics"]["valid sharpe"] for r in s["tracker"].runs()])
    champ = s["champion"]
    test_sr, _ = sharpe(fit(champ["params"], champ["seed"], "2026-01", "v1"), "2026-01", "v1",
                        range(TRAIN + VALID, DAYS))
    sr_p = champ["metrics"]["valid sharpe"] / math.sqrt(252)
    return {"runs": len(vals), "trials logged": s["log"].trial_count("gbdt tuning"), "best valid": float(vals.max()),
            "median valid": float(np.median(vals)), "test": test_sr,
            "dsr 200": s["log"].deflated("gbdt tuning", sr_p, VALID), "psr 1": _psr(sr_p, VALID)}


def _psr(sr_p, n):
    from firm_researchlog import deflated_sharpe

    return deflated_sharpe(sr_p, n)


def reproduction():
    """From the registry entry as of a March morning, back to the run record, and a bitwise re-run; then each field
    replaced by an assumption."""
    s = study()
    entry = s["registry"].as_of("xs-gbdt", "2026-03-10T08:00")
    rec = s["tracker"].get(entry["run"])
    out = {"registry": reproduce(rec, train)[1]}
    assume = {"params": dict(DEFAULTS), "seed": 1, "data": "2026-03", "code": "v2"}
    base_sr, _ = sharpe(fit(rec["params"], rec["seed"], "2026-01", "v1"), "2026-01", "v1", range(TRAIN + VALID, DAYS))
    for f in ("params", "seed", "data", "code"):
        r2 = dict(rec) | {f: assume[f]}
        h, same = reproduce(r2, train)
        sr, _ = sharpe(fit(r2["params"], r2["seed"], r2["data"], r2["code"]), "2026-01", "v1" if f != "code" else "v2",
                       range(TRAIN + VALID, DAYS))
        out[f] = (same, sr - base_sr)
    out["audit intact"] = s["audit"].verify() == -1
    return out


def fields():
    return FIELDS


def null_max():
    """The expected maximum annualised Sharpe ratio of 200 strategies with no skill, over 150 validation days."""
    from firm_multitest import expected_max_sr

    return expected_max_sr(N_RUNS, 1.0 / VALID) * math.sqrt(252)


def seed_spread(seeds=range(1, 11)):
    """Exercise 7: the champion's configuration retrained with ten seeds, test Sharpe ratios."""
    c = study()["champion"]
    return [sharpe(fit(c["params"], s, "2026-01", "v1"), "2026-01", "v1", range(TRAIN + VALID, DAYS))[0] for s in seeds]
