"""Build: an order-book model, end to end (One Quant Book 12, chapter 29).

The whole pipeline of firm.lobmodel run as one firm.workflow graph on Book 10's exchange simulator: eight training,
three validation and six test sessions of twenty minutes on disjoint seeds; ten features through firm.featstore;
one-second labels through firm.labeling; LightGBM chosen by purged cross-validation against a small TCN; the forest
compiled (firm.mlinfer; C++20 and Rust parity in firm.lobmodel); a threshold chosen on the validation sessions; then
the test sessions traded at ten decision latencies, from the compiled model's measured 150 nanoseconds to 150
milliseconds, and without a model. The run is tracked in firm.exptrack and the test sessions pass chapter 27's input
monitors."""
from __future__ import annotations

import functools
import os
import pathlib
import sys
import tempfile

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402

_FIRM = pathlib.Path(__file__).resolve().parents[3] / "firm"
for _c in ("lobmodel", "exptrack", "mlmonitor", "researchlog"):
    sys.path.insert(0, str(_FIRM / _c))
import firm_lobmodel as lm  # noqa: E402
from firm_exptrack import AuditTrail, Registry, Tracker  # noqa: E402
from firm_mlmonitor import Reference, psi  # noqa: E402

CFG = lm.DEFAULT
MEASURED = (pathlib.Path(__file__).resolve().parents[4] / "figdata" / "ml" / "29-build-an-order-book-model-end-to-end"
            / "measured_latency.csv")
_CACHE = tempfile.mkdtemp(prefix="ml29-")


@functools.lru_cache(maxsize=1)
def run():
    """Outputs and manifest of the whole graph (computed once per process, about three minutes on one core)."""
    return lm.make_pipeline(_CACHE, CFG).run()


def outputs():
    return run()[0]


def summary():
    o = outputs()
    return {"train rows": len(o["train"]["y"]), "valid rows": len(o["valid"]["y"]), "cv": o["cv"]["scores"],
            "chosen leaves": o["cv"]["chosen"]["num_leaves"], "valid ic": o["fit"]["valid ic"],
            "train ic": o["fit"]["train ic"], "tcn ic": o["tcn"]["valid ic"], "tcn params": o["tcn"]["parameters"],
            "trees": len(o["fit"]["forest"]["roots"]), "nodes": len(o["fit"]["forest"]["feature"]),
            "parity": float(np.max(np.abs(o["fit"]["lightgbm"] - o["fit"]["flat"]))),
            "threshold pnl": o["threshold"]["pnl"], "threshold": o["threshold"]["chosen"],
            "zero moves": float(np.mean(o["train"]["y"] == 0)),
            "tick moves": float(np.mean(np.abs(o["train"]["y"]) >= 1))}


def latency_table():
    """Per decision latency: mean net P&L per session and its standard error over the six test sessions, the mean
    one-second mark-out of entries (ticks), entries per session, and the median decision staleness (ms)."""
    t = outputs()["test"]
    rows = []
    for lat, rs in zip(t["latency ns"], t["model"], strict=True):
        p = np.array([r["pnl"] for r in rs])
        rows.append({"latency ms": lat / 1e6, "pnl": float(p.mean()), "se": float(p.std(ddof=1) / np.sqrt(len(p))),
                     "markout 1 s": float(np.mean([r["markout"][1.0] for r in rs])),
                     "markout 0.1 s": float(np.mean([r["markout"][0.1] for r in rs])),
                     "entries": float(np.mean([r["entries"] for r in rs])),
                     "staleness ms": float(np.median([r["staleness ms"] for r in rs])),
                     "positive sessions": int(np.sum(p > 0)), "fees": float(np.mean([r["fees"] for r in rs]))})
    nm = t["no model"]
    p = np.array([r["pnl"] for r in nm])
    base = {"pnl": float(p.mean()), "se": float(p.std(ddof=1) / np.sqrt(len(p))),
            "markout 1 s": float(np.mean([r["markout"][1.0] for r in nm])),
            "entries": float(np.mean([r["entries"] for r in nm])), "fees": float(np.mean([r["fees"] for r in nm]))}
    return rows, base


def zero_crossing(target="pnl", level=0.0):
    """The decision latency (ms) at which the mean P&L (or another column) first falls to `level`, by linear
    interpolation between grid points."""
    rows, _ = latency_table()
    for a, b in zip(rows, rows[1:], strict=False):
        if a[target] > level >= b[target]:
            w = (a[target] - level) / (a[target] - b[target])
            return a["latency ms"] + w * (b["latency ms"] - a["latency ms"])
    return None


def measured():
    rows = np.genfromtxt(MEASURED, delimiter=",", names=True, dtype=None, encoding=None)
    return {str(r["path"]): float(r["median_ns"]) for r in rows}


def tracking(root):
    """The run in firm.exptrack: one record with the pipeline's stage keys as code, the fitted forest as artefact, and
    the registered version promoted with its test result as the reason."""
    o, man = run()
    trail = AuditTrail(pathlib.Path(root) / "audit.jsonl")
    tr = Tracker(root)
    rows, _ = latency_table()
    rid = tr.run(params={"cfg": {k: str(v) for k, v in CFG.items()}}, seed=1, data=man["stages"]["train"]["output"],
                 code=man["stages"]["fit"]["key"], env=man["env"],
                 metrics={"valid ic": o["fit"]["valid ic"], "test pnl": rows[1]["pnl"]},
                 artefact=o["fit"]["forest"], ts="2026-09-26T12:00")
    reg = Registry(root, trail)
    v = reg.register("lob-mid-forest", rid, tr.get(rid), "2026-09-26T12:00")
    reg.promote("lob-mid-forest", v, "production", "2026-09-26T12:05", "test sessions positive at 150 ns")
    return rid, reg.lineage("lob-mid-forest", v), trail.verify()


PRICE = (0, 1, 7, 8)                                              # imbalance, spread, the two mid changes


@functools.lru_cache(maxsize=1)
def monitors():
    """Chapter 27's input monitor on the test sessions' recorded features, each session against the training sessions:
    per session, the largest population stability index over all ten features, the feature that gives it, and the
    largest over the four price features (the rest count events, and move with the session's activity)."""
    tr = outputs()["train"]["X"]
    refs = [Reference(tr[:, j]) for j in range(tr.shape[1])]
    out = []
    for s in CFG["test"]:
        ev, times = lm.record(s, CFG["seconds"])
        X = lm.offline(ev, lm.FEATURES, times)
        v = [psi(refs[j], X[:, j]) for j in range(X.shape[1])]
        out.append({"max": max(v), "feature": lm.FEATURES[int(np.argmax(v))].name,
                    "price max": max(v[j] for j in PRICE),
                    "decisions": len(times)})
    return out
