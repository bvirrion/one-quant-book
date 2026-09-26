"""Alternative-data pipelines (One Quant Book 12, chapter 15).

A synthetic card-spending panel on 100 retailers over 24 quarters (firm.altdata.card_panel): the vendor launches at
quarter 12 with a history backfilled with hindsight, and changes bank partner at quarter 16. Deliveries arrive as rows
with merchant strings and planted defects; the pipeline validates them, resolves the strings to permanent identifiers,
stores what it learns with first-seen timestamps (firm.pit), and nowcasts each retailer's year-on-year sales growth from
spend per panelist, raw and raked to the population's margins. The nowcast is scored against the truth, and against
announcement returns through its information coefficient, on backfilled and on live history."""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

_FIRM = pathlib.Path(__file__).resolve().parents[3] / "firm"
for _c in ("altdata", "pit", "vendoreval"):
    sys.path.insert(0, str(_FIRM / _c))
from firm_altdata import card_panel, delivery_check, first_seen, rake, resolve, validate  # noqa: E402
from firm_pit import Store  # noqa: E402
from firm_vendoreval import rank_ic  # noqa: E402

Q, LAUNCH, CHANGE, N_FIRMS = 24, 12, 16, 100
CENTS_QUARTER = 19                                                     # the delivery sent in cents


@functools.lru_cache(maxsize=1)
def world():
    return card_panel(N_FIRMS, Q, LAUNCH, CHANGE, seed=0)


def _vendor_values():
    """What the vendor delivers per firm, quarter and cell: the panel, except that the history it could check at
    launch (quarters whose sales were already reported, before the last one) was moved three quarters of the way
    towards the reported sales when the vendor built it."""
    w = world()
    panel = w["panel"].copy()
    est = np.einsum("iqar,ar->iq", panel / w["panelists"][None], w["pop"])
    shrink = (w["sales"] / est) ** 0.75
    panel[:, :LAUNCH - 1] *= shrink[:, :LAUNCH - 1, None, None]
    return panel


@functools.lru_cache(maxsize=1)
def deliveries(seed=1):
    """{delivery quarter: rows}. Each firm-quarter-cell's spend is split across two or three merchant strings. Planted
    defects: 0.3% of rows lose a field, 0.2% have a negative spend, 0.2% carry the panel count as text, 0.3% are
    duplicated, and the delivery for quarter 19 is in cents."""
    rng = np.random.default_rng(seed)
    w = world()
    vals = _vendor_values()
    out = {}
    for q in range(Q):
        known = LAUNCH if q < LAUNCH else q + 1
        rows = out.setdefault(known, [])
        for i in range(N_FIRMS):
            for a in range(3):
                for r in range(2):
                    k = int(rng.integers(2, 4))
                    parts = rng.dirichlet(np.ones(k))
                    strs = rng.choice(w["strings"][i], k, replace=False)
                    for p, s in zip(parts, strs, strict=True):
                        spend = float(vals[i, q, a, r] * p) * (100.0 if q == CENTS_QUARTER else 1.0)
                        row = {"quarter": q, "merchant": str(s), "age": a, "region": r, "spend": spend,
                               "panelists": int(w["panelists"][q, a, r]), "_firm": i}
                        u = rng.random()
                        if u < 0.003:
                            del row[["merchant", "spend", "panelists"][rng.integers(3)]]
                            row["_defect"] = "missing"
                        elif u < 0.005:
                            row["spend"], row["_defect"] = -row["spend"], "range"
                        elif u < 0.007:
                            row["panelists"], row["_defect"] = str(row["panelists"]), "type"
                        elif u < 0.010:
                            rows.append(dict(row) | {"_defect": "duplicate"})
                        rows.append(row)
        for s in w["distractors"]:                                     # merchants that are not the retailers
            for a in range(3):
                rows.append({"quarter": q, "merchant": s, "age": a, "region": int(rng.integers(2)),
                             "spend": float(rng.lognormal(8, 1)) * (100.0 if q == CENTS_QUARTER else 1.0),
                             "panelists": int(w["panelists"][q, a, 0]), "_firm": -1})
    return out


@functools.lru_cache(maxsize=2)
def ingest(review=True):
    """Validate every delivery, hold a delivery whose total moves by more than a factor 2 from the previous live one
    (then rescale it after review), resolve the merchant strings, and store spend by firm, quarter and cell with the
    delivery quarter as knowledge time."""
    w = world()
    aliases = {name: i for i, name in enumerate(w["names"])}
    strings = sorted({r["merchant"] for rows in deliveries().values() for r in rows if "merchant" in r})
    res = resolve(strings, aliases)
    store = Store()
    stats = {"rows": 0, "rejects": {}, "held": [], "strings": len(strings)}
    prev = None
    for known in sorted(deliveries()):
        clean, rej = validate(deliveries()[known])
        stats["rows"] += len(deliveries()[known])
        for _, why in rej:
            key = why.split()[0]
            stats["rejects"][key] = stats["rejects"].get(key, 0) + 1
        total = sum(r["spend"] for r in clean)
        scale = 1.0
        if known > LAUNCH and not delivery_check(prev, total):
            stats["held"].append(known)
            scale = 0.01                                                # review finds the unit change
        if known > LAUNCH:
            prev = total * scale
        agg = {}
        for r in clean:
            pid = reviewed(res, r["merchant"]) if review else (res[r["merchant"]][0]
                                                                  if res[r["merchant"]][2] == "matched" else None)
            if pid is None:
                continue
            key = (pid, r["quarter"], r["age"], r["region"])
            agg[key] = agg.get(key, 0.0) + r["spend"] * scale
        for (pid, q, a, rg), v in agg.items():
            store.put(pid, "spend", (q, a, rg), known, v)
    return store, res, stats


def truth_map():
    w = world()
    return {s: i for i, ss in w["strings"].items() for s in ss} | {s: None for s in w["distractors"]}


def reviewed(res, s):
    """The identifier used downstream: the match if matched, a person's decision (the truth) if in the review queue,
    nothing otherwise."""
    pid, _, status = res[s]
    if status == "matched":
        return pid
    if status == "review":
        return truth_map()[s]
    return None


def resolution_quality():
    """Status shares, precision of automatic matches, and what the exact-name baseline would have matched, over the
    retailers' strings and the distractors."""
    from firm_altdata import normalise

    w = world()
    _, res, _ = ingest()
    truth = truth_map()
    ret = [s for s in res if truth.get(s, "x") is not None and s in truth]
    dis = [s for s in res if s in truth and truth[s] is None]
    names = {normalise(n) for n in w["names"]}
    return {"retailer strings": len(ret), "distractors": len(dis),
            "retailer status": {k: sum(res[s][2] == k for s in ret) for k in ("matched", "review", "none")},
            "distractor status": {k: sum(res[s][2] == k for s in dis) for k in ("matched", "review", "none")},
            "wrong matches": sum(res[s][2] == "matched" and res[s][0] != truth[s] for s in ret + dis),
            "exact matches": sum(normalise(s) in names for s in ret)}


@functools.lru_cache(maxsize=2)
def panel_table(review=True):
    """Spend by firm, quarter and cell as last known (arrays), rebuilt from the store."""
    store, _, _ = ingest(review)
    X = np.full((N_FIRMS, Q, 3, 2), np.nan)
    for i in range(N_FIRMS):
        for (q, a, r), v in store.latest(i, "spend").items():
            X[i, q, a, r] = v
    return X


def estimates(method, review=True):
    """Spend per head of population implied by the panel: 'raw' divides each firm's panel spend by the number of
    panelists; 'raked' weights the cells so that the panel matches the population's age and region margins."""
    w = world()
    X, n = panel_table(review), w["panelists"]
    out = np.zeros((N_FIRMS, Q))
    for q in range(Q):
        if method == "raw":
            wt = np.ones((3, 2))
        else:
            wt = rake(n[q], w["pop"].sum(1), w["pop"].sum(0))
        out[:, q] = np.nansum(X[:, q] * wt[None], axis=(1, 2)) / (wt * n[q]).sum()
    return out


def growth(x):
    g = np.full_like(x, np.nan)
    g[:, 4:] = x[:, 4:] / x[:, :-4] - 1
    return g


@functools.lru_cache(maxsize=2)
def errors(method):
    """Mean absolute error of the nowcast year-on-year growth (percentage points), by quarter."""
    true = growth(world()["sales"])
    out = np.full(Q, np.nan)
    out[4:] = 100 * np.mean(np.abs(growth(estimates(method)) - true)[:, 4:], axis=0)
    return out


def error_summary():
    out = {}
    for m in ("raw", "raked"):
        e = errors(m)
        out[m] = {"quarters 4-15": float(np.mean(e[4:CHANGE])), "quarters 16-19": float(np.mean(e[CHANGE:CHANGE + 4])),
                  "quarters 20-23": float(np.mean(e[CHANGE + 4:]))}
    return out


@functools.lru_cache(maxsize=1)
def returns(seed=2):
    """Consensus = true growth + analyst error (3%); announcement return = 1 x (true - consensus) + noise (4%)."""
    rng = np.random.default_rng(seed)
    true = growth(world()["sales"])
    cons = true + 0.03 * rng.standard_normal(true.shape)
    ret = (true - cons) + 0.04 * rng.standard_normal(true.shape)
    return cons, ret


def ic_by_quarter(method):
    cons, ret = returns()
    g = growth(estimates(method))
    return np.array([rank_ic(g[:, q] - cons[:, q], ret[:, q]) if q >= 4 else np.nan for q in range(Q)])


def backfilled_quarters():
    """Quarters whose data were first seen more than one quarter after they ended (firm.pit first-seen times)."""
    store, _, _ = ingest()
    return [q for q in range(Q) if first_seen(store, 0, "spend", (q, 0, 0)) - q > 1]


def ic_summary():
    bf = [q for q in backfilled_quarters() if q >= 4]
    live_pre = list(range(LAUNCH, CHANGE))
    live_post = list(range(CHANGE, Q))
    out = {}
    for m in ("raw", "raked"):
        ic = ic_by_quarter(m)
        out[m] = {"backfilled": float(np.mean(ic[bf])), "live before the change": float(np.mean(ic[live_pre])),
                  "live after the change": float(np.mean(ic[live_post])),
                  "live": float(np.mean(ic[LAUNCH:]))}
    return out


def planted_defects():
    out = {}
    for rows in deliveries().values():
        for r in rows:
            if "_defect" in r:
                out[r["_defect"]] = out.get(r["_defect"], 0) + 1
    return out


def rake_example():
    """Exercise: a 2 x 2 panel raked to even margins."""
    w = rake([[30, 20], [10, 40]], [0.5, 0.5], [0.5, 0.5])
    return w, w * np.array([[30, 20], [10, 40]])


def errors_without_review():
    """Exercise 7: the raked nowcast's mean error (points) when strings in the review queue are dropped, and the share
    of the retailers' delivered spend that sat in those strings."""
    true = growth(world()["sales"])
    e = np.abs(growth(estimates("raked", review=False)) - true)[:, 4:] * 100
    _, res, _ = ingest()
    rows = [r for rows in deliveries().values() for r in rows if r.get("_firm", -1) >= 0 and "merchant" in r
            and isinstance(r.get("spend"), float) and r["spend"] > 0]
    lost = sum(r["spend"] for r in rows if res[r["merchant"]][2] == "review") / sum(r["spend"] for r in rows)
    return float(e.mean()), float(lost)
