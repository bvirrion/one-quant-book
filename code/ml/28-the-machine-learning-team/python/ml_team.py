"""The machine-learning team (One Quant Book 12, chapter 28).

Part 1, the handoff: a package for chapter 26's compiled forest (artefact, 16 feature definitions, test vectors, a
latency budget, monitors, a model card) is validated as a continuous-integration job would, then eight defects a
handoff typically carries are planted one at a time. Part 2, the pipeline: a research-to-production pipeline simulated
as a network of queues with rework loops and kill gates, its lead times and losses, and the same pipeline once the
reimplementation handoff is replaced by the package. A single M/M/1 station is checked against Book 4's chain tools."""
from __future__ import annotations

import copy
import functools
import json
import os
import pathlib
import sys
import tempfile

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402

_FIRM = pathlib.Path(__file__).resolve().parents[3] / "firm"
for _c in ("modelpkg", "featstore", "tape", "workflow", "modelcard", "queues"):
    sys.path.insert(0, str(_FIRM / _c))
from firm_featstore import FeatureDef, events_from_tape, offline  # noqa: E402
from firm_modelcard import CARD_FIELDS  # noqa: E402
from firm_modelpkg import Station, load, simulate_pipeline, validate  # noqa: E402
from firm_queues import generator, stationary  # noqa: E402
from firm_tape import TapeConfig, simulate  # noqa: E402
from firm_workflow import content_hash  # noqa: E402

PACKAGE = pathlib.Path(__file__).resolve().parents[1] / "package"
FEATURES = (FeatureDef("spread", "spread", "last"), FeatureDef("imbalance", "imbalance", "last"),
            FeatureDef("depth imbalance", "depth", "last"), FeatureDef("weighted mid minus mid", "wmid", "last"),
            FeatureDef("OFI 1 s", "ofi", "sum", 1), FeatureDef("OFI 5 s", "ofi", "sum", 5),
            FeatureDef("OFI 30 s", "ofi", "sum", 30), FeatureDef("volume 5 s", "trade_qty", "sum", 5),
            FeatureDef("volume 30 s", "trade_qty", "sum", 30),
            FeatureDef("signed volume 30 s", "trade_sign", "sum", 30),
            FeatureDef("trades 10 s", "is_trade", "sum", 10), FeatureDef("trades 30 s", "is_trade", "sum", 30),
            FeatureDef("mid change 1 s", "mid", "change", 1), FeatureDef("mid change 5 s", "mid", "change", 5),
            FeatureDef("mid change 30 s", "mid", "change", 30), FeatureDef("messages 10 s", "one", "sum", 10))


@functools.lru_cache(maxsize=1)
def reference_session():
    """A two-minute firm.tape session and the decision times (trades after the first 30 seconds) the feature checks
    run on."""
    ev = events_from_tape(simulate(TapeConfig(seconds=120.0, news_at=None, seed=2800)))
    ev["is_trade"] = ev["is_trade"].astype(float)
    times = np.unique(ev["t"][ev["is_trade"] > 0])
    return ev, times[times >= 30.0]


def manifest():
    art = _FIRM / "mlinfer" / "data" / "forest.txt"
    return {
        "name": "mid-forecast-forest", "version": 3,
        "artefact": "../../../firm/mlinfer/data/forest.txt", "artefact_hash": content_hash(art.read_bytes()),
        "features": [{"name": f.name, "input": f.input, "agg": f.agg, "window": f.window, "version": f.version}
                     for f in FEATURES],
        "feature_vectors": "feature_vectors.csv",
        "test_vectors": "../../../firm/mlinfer/data/vectors.csv", "tolerance": 1e-12,
        "latency_budget_us": 5.0, "latency_measured_us": 2.6,
        "monitoring": [{"statistic": s, "threshold": th, "pages_per_month": 1, "owner": o} for s, th, o in
                       (("feature psi", 0.115, "data"), ("prediction psi", 0.089, "desk"),
                        ("inside threshold", 0.07, "desk"), ("ic cusum", 0.11, "model owner"))],
        "card": {f: f"see chapter 26 ({f})" for f in CARD_FIELDS} | {"name": "mid-forecast-forest", "version": "3"},
    }


def write_package(path=PACKAGE):
    """The package directory: manifest.json and research's feature values on the reference session."""
    path = pathlib.Path(path)
    path.mkdir(parents=True, exist_ok=True)
    (path / "manifest.json").write_text(json.dumps(manifest(), indent=1, sort_keys=True) + "\n")
    ev, times = reference_session()
    np.savetxt(path / "feature_vectors.csv", offline(ev, FEATURES, times), delimiter=",", fmt="%.17g")


def check(pkg):
    ev, times = reference_session()
    return validate(pkg, ev, times)


def _defects():
    """Eight defects a handoff carries, each a function that edits a loaded package (and may write files)."""
    def rebuilt(p, d):                                                   # the artefact changed after it was hashed
        f = pathlib.Path(d) / "forest.txt"
        lines = pathlib.Path(p["artefact"]).read_text().splitlines()
        vals = lines[-1].split()
        vals[1] = repr(float(vals[1]) * 1.01)
        f.write_text("\n".join(lines[:-1] + [" ".join(vals)]) + "\n")
        p["artefact"] = str(f)

    def unknown_input(p, d):
        p["features"][3] = {"name": "microprice minus mid", "input": "microprice", "agg": "last", "window": 0.0}

    def milliseconds(p, d):
        p["features"][5]["window"] = 5000.0                               # 5 s written as 5,000 ms

    def missing_feature(p, d):
        p["features"].pop()

    def stale_vectors(p, d):                                            # expected outputs of another model
        V = np.loadtxt(p["test_vectors"], delimiter=",")
        V[:, 16] = V[:, 17]
        f = pathlib.Path(d) / "vectors.csv"
        np.savetxt(f, V, delimiter=",", fmt="%.17g")
        p["test_vectors"] = str(f)

    def over_budget(p, d):
        p["latency_measured_us"] = 265.0                                 # the library call, not the compiled model

    def unowned_monitor(p, d):
        del p["monitoring"][3]["owner"]

    def no_limitations(p, d):
        p["card"]["limitations"] = ""

    return {"artefact rebuilt after hashing": rebuilt, "input the feed does not carry": unknown_input,
            "window in milliseconds": milliseconds, "one feature missing": missing_feature,
            "another model's test vectors": stale_vectors, "library latency": over_budget,
            "monitor without owner": unowned_monitor, "card without limitations": no_limitations}


@functools.lru_cache(maxsize=1)
def handoff_table():
    """For the clean package and each defect: the checks that fail."""
    base = load(PACKAGE / "manifest.json")
    out = {"clean": [c for c, ok, _ in check(base) if not ok]}
    with tempfile.TemporaryDirectory() as d:
        for name, fn in _defects().items():
            p = copy.deepcopy(base)
            fn(p, d)
            out[name] = [c for c, ok, _ in check(p) if not ok]
    return out


def checks_run():
    return [c for c, _, _ in check(load(PACKAGE / "manifest.json"))]


# ---------------------------------------------------------------------------------------------------- pipeline
def stations(handoff=True):
    """Weeks. The main line: review, reimplementation (or integration of a package), validation, paper trading,
    canary; side loops (names starting '~') for rework with the researcher."""
    build = (Station("reimplementation", 2, 4.0, kill=0.05, rework=0.30, rework_to=6) if handoff else
             Station("integration", 2, 1.0, kill=0.05, rework=0.05, rework_to=6))
    return (Station("review", 1, 0.6, kill=0.35, rework=0.15, rework_to=5), build,
            Station("validation", 1, 1.5, kill=0.10, rework=0.25 if handoff else 0.10, rework_to=1),
            Station("paper trading", 0, 4.0, kill=0.20, dist="fixed"),
            Station("canary", 0, 2.0, kill=0.05, dist="fixed"),
            Station("~research fixes", 0, 2.0, next_to=0), Station("~clarification", 0, 1.5, next_to=1))


RATE, N_MODELS, BURN = 0.35, 4000, 500


@functools.lru_cache(maxsize=64)
def pipeline(handoff=True, package_weeks=0.0, seed=0, rate=None):
    """Median and quartiles of lead time (weeks from the end of research to production) of the models that reach
    production, the share of all models lost at each gate, the mean visits to the build station, and Little's law.
    package_weeks: extra research time spent building the package, added to every lead time."""
    st = stations(handoff)
    rate = RATE if rate is None else rate
    r = simulate_pipeline(st, rate, N_MODELS, seed)
    keep = slice(BURN, None)                                             # the pipeline starts empty: drop the first 500
    arr, done, kill = r["arrival"][keep], r["done"][keep], r["killed_at"][keep]
    ok = np.isfinite(done)
    lead = done[ok] - arr[ok] + package_weeks
    lost = {st[k].name: float(np.mean(kill == k)) for k in range(5)}
    return {"median": float(np.median(lead)), "q25": float(np.quantile(lead, 0.25)),
            "q75": float(np.quantile(lead, 0.75)), "q90": float(np.quantile(lead, 0.9)),
            "reach": float(ok.mean()), "lost": lost, "build visits": float(r["visits"][keep][:, 1][kill != 0].mean()),
            "build utilisation": float(rate * r["visits"][keep][:, 1].mean() * st[1].mean / st[1].servers),
            "lead": lead}


def rate_curve(rates=(0.2, 0.25, 0.3, 0.35, 0.4, 0.42, 0.44), seeds=3):
    """Median lead time against the arrival rate, averaged over seeds, with and without the handoff (the package
    adds one week of research time)."""
    out = {}
    for h, extra in ((True, 0.0), (False, 1.0)):
        out[h] = [float(np.mean([pipeline(h, extra, s, r)["median"] for s in range(seeds)])) for r in rates]
    return rates, out


def third_engineer(seeds=3):
    """Exercise 7: the rewrite kept, a third engineer added; median lead time and utilisation, means over seeds."""
    st = list(stations(True))
    st[1] = Station("reimplementation", 3, 4.0, kill=0.05, rework=0.30, rework_to=6)
    meds, util = [], []
    for s in range(seeds):
        r = simulate_pipeline(tuple(st), RATE, N_MODELS, s)
        a, d = r["arrival"][BURN:], r["done"][BURN:]
        ok = np.isfinite(d)
        meds.append(float(np.median(d[ok] - a[ok])))
        util.append(float(RATE * r["visits"][BURN:, 1].mean() * 4.0 / 3))
    return float(np.mean(meds)), float(np.mean(util))


def lead_by_stage(handoff=True):
    """Where the time goes: mean weeks per model reaching production, waiting versus served, per main station,
    estimated by re-simulating with every station's servers made unlimited (the service-only lead time)."""
    base = pipeline(handoff)["median"]
    st = stations(handoff)
    free = tuple(Station(s.name, 0, s.mean, s.kill, s.rework, s.rework_to, s.dist, s.next_to) for s in st)
    r = simulate_pipeline(free, RATE, N_MODELS, 0)
    ok = np.isfinite(r["done"][BURN:])
    return {"median": base, "no queues": float(np.median((r["done"] - r["arrival"])[BURN:][ok]))}


def mm1_check(lam=0.8, mu=1.0, n=200_000, seed=1):
    """One M/M/1 station simulated against theory: mean time in system 1/(mu - lam), and the number in system against
    the stationary law of Book 4's birth-death chain (truncated at 60)."""
    r = simulate_pipeline((Station("one", 1, 1 / mu),), lam, n, seed)
    a, d = r["arrival"][1000:], r["done"][1000:]
    W = float(np.mean(d - a))
    m = 61
    rates = np.zeros((m, m))
    for k in range(m - 1):
        rates[k, k + 1], rates[k + 1, k] = lam, mu
    pi = stationary(generator(rates))
    L_chain = float(np.sum(np.arange(m) * pi))
    return {"W sim": W, "W theory": 1 / (mu - lam), "L chain": L_chain, "L little": lam * W, "p0 chain": float(pi[0])}


def littles_law(handoff=True):
    """Little's law on the whole pipeline: the time-average number of models in it (arrival to production or kill)
    against the arrival rate times the mean time in it, over the arrivals after the first 500."""
    r = simulate_pipeline(stations(handoff), RATE, N_MODELS, 0)
    a, e = r["arrival"][BURN:], r["exit"][BURN:]
    t0, t1 = a[0], a[-1]
    grid = np.linspace(t0, t1, 4001)
    wip = np.array([np.sum((a <= g) & (e > g)) for g in grid])
    inside = (a >= t0) & (e <= t1)
    return {"wip": float(wip.mean()), "rate x time": float(RATE * np.mean((e - a)[inside])),
            "mean time": float(np.mean((e - a)[inside]))}
