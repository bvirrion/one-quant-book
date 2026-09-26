"""firm.altdata -- an alternative-data pipeline: ingest, validate, resolve, reweight, detect backfill (Book 12,
chapter 15).

A synthetic card-spending panel with a known truth: retailers' true quarterly sales are spent by six demographic cells
(three age bands times two regions) of a population with known margins; a vendor's panel samples the cells with a tilt
that drifts, changes bank partner at a chosen quarter, delivers rows with merchant strings rather than identifiers, and
launches with a history backfilled after the fact. The pipeline validates each delivery against a schema and against
the previous delivery, resolves merchant strings to permanent identifiers with a review queue, reweights the panel to
the population margins by raking, and separates backfilled from live history by first-seen timestamps in firm.pit.

API (stable):
    SCHEMA; validate(rows, schema) -> (clean, rejects)            rejects: (row, reason)
    delivery_check(prev_total, new_total, lo, hi) -> bool          a delivery's total within [lo, hi] x the last
    normalise(merchant) -> str; similarity(a, b) -> float in [0, 1]
    resolve(strings, aliases, accept, review) -> {string: (pid or None, score, status)}   status matched/review/none
    rake(counts, row_margin, col_margin, iters) -> cell weights so that weighted counts match both margins
    first_seen(store, entity, field, valid) -> knowledge time of the first delivery (firm.pit)
    card_panel(n_firms, quarters, launch, partner_change, seed) -> dict (truth, rows, deliveries, population)
"""
from __future__ import annotations

import difflib
import pathlib
import re
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "pit"))
from firm_pit import Store  # noqa: E402, F401  (re-exported: the store first_seen reads)

SCHEMA = {"quarter": (int, lambda v: v >= 0), "merchant": (str, lambda v: len(v) > 0),
          "age": (int, lambda v: v in (0, 1, 2)), "region": (int, lambda v: v in (0, 1)),
          "spend": (float, lambda v: v >= 0), "panelists": (int, lambda v: v > 0)}


def validate(rows, schema=SCHEMA):
    """Keep the rows whose every field is present, of the right type and in range; drop exact duplicates."""
    clean, rejects, seen = [], [], set()
    for r in rows:
        reason = None
        for f, (typ, ok) in schema.items():
            v = r.get(f)
            if v is None:
                reason = f"missing {f}"
            elif not isinstance(v, typ) or isinstance(v, bool):
                reason = f"type {f}"
            elif not ok(v):
                reason = f"range {f}"
            if reason:
                break
        key = tuple(r.get(f) for f in schema)
        if reason is None and key in seen:
            reason = "duplicate"
        if reason:
            rejects.append((r, reason))
        else:
            seen.add(key)
            clean.append(r)
    return clean, rejects


def delivery_check(prev_total, new_total, lo=0.5, hi=2.0):
    """A delivery whose total spend moves by more than a factor 2 from the previous one is held for review (a unit
    change, a lost file, a duplicated file)."""
    return prev_total is None or lo <= new_total / prev_total <= hi


_NOISE = re.compile(r"^(sq|tst|pp|pos)\s*\*\s*|#\s*\d+|\b\d+\b|\b(inc|corp|co|ltd|llc|online|store|str)\b")


def normalise(merchant):
    s = _NOISE.sub(" ", merchant.lower().replace(".", " "))
    return " ".join(re.sub(r"[^a-z ]", " ", s).split())


def similarity(a, b):
    """Token-level match of a merchant string a against an alias b: each alias token scores 1 if some token of a is
    equal to it or a prefix of it of at least three letters (card networks truncate), else its best character-level
    ratio; the score is the mean over the alias's tokens, less a penalty for tokens of a that match nothing."""
    ta, tb = a.split(), b.split()
    if not ta or not tb:
        return 0.0

    def tok(x, y):
        if x == y or (len(x) >= 3 and y.startswith(x)):
            return 1.0
        return difflib.SequenceMatcher(None, x, y).ratio()

    cover = float(np.mean([max(tok(x, y) for x in ta) for y in tb]))
    extra = sum(max(tok(x, y) for y in tb) < 0.8 for x in ta) / len(ta)
    return cover * (1 - 0.5 * extra)


def resolve(strings, aliases, accept=0.9, review=0.5):
    """aliases: {alias text: pid}. Each merchant string is normalised and compared with every normalised alias; the best
    score above `accept` is a match, between `review` and `accept` goes to a person, below is unmatched. A tie between
    two companies above `review` also goes to review."""
    norm = [(normalise(a), pid) for a, pid in aliases.items()]
    out = {}
    for s in strings:
        n = normalise(s)
        scored = sorted(((similarity(n, a), pid) for a, pid in norm), reverse=True)
        best, pid = scored[0]
        rival = next((sc for sc, p in scored[1:] if p != pid), 0.0)
        if best >= accept and best - rival > 1e-9:
            out[s] = (pid, best, "matched")
        elif best >= review:
            out[s] = (pid, best, "review")
        else:
            out[s] = (None, best, "none")
    return out


def rake(counts, row_margin, col_margin, iters=50):
    """Iterative proportional fitting: weights w (cells, same shape as counts) such that the weighted counts' row sums
    match row_margin and column sums match col_margin (margins as shares or totals, rescaled to the panel's total)."""
    counts = np.asarray(counts, dtype=float)
    tot = counts.sum()
    r = np.asarray(row_margin, float) / np.sum(row_margin) * tot
    c = np.asarray(col_margin, float) / np.sum(col_margin) * tot
    w = np.ones_like(counts)
    for _ in range(iters):
        w *= (r / (w * counts).sum(1))[:, None]
        w *= (c / (w * counts).sum(0))[None, :]
    return w


def first_seen(store, entity, field, valid):
    row = store.first(entity, field, valid)
    return None if row is None else row[0]


# ---------------------------------------------------------------------------------------------------- the world
_STEMS = ["Borealis", "Cobalt", "Delta", "Ember", "Fulcrum", "Granite", "Harbor", "Ionic", "Juniper", "Keystone",
          "Lumen", "Meridian", "Nimbus", "Orion", "Pinnacle", "Quartz", "Redwood", "Summit", "Tidal", "Umbra",
          "Vertex", "Willow", "Xenon", "Yarrow", "Zephyr", "Apex", "Beacon", "Crescent", "Dune", "Everest",
          "Falcon", "Glacier", "Horizon", "Indigo", "Jasper", "Kestrel", "Laurel", "Monarch", "Nova", "Opal"]
_KIND = ["Retail", "Stores", "Outfitters", "Market", "Foods"]


def _strings(rng, name):
    """Merchant strings as a card network prints them: prefixes, store numbers, truncation, abbreviations, and the
    first word alone."""
    stem, kind = name.split()
    forms = [f"{name.upper()} #{rng.integers(100, 9999)}", f"SQ *{stem.upper()} {kind.upper()[:3]}",
             f"{stem.upper()} {kind.upper()} {rng.integers(10, 99)} ONLINE", f"TST* {stem} {kind} Inc",
             f"{stem.upper()[:7]} {kind.upper()[:4]} STR {rng.integers(1, 999)}",
             f"{stem.upper()} {rng.integers(1000, 9999)}"]
    return forms


DISTRACTORS = ["DELTA AIR LINES 0062", "SUMMIT DENTAL CARE", "SQ *HARBOR CAFE", "ORION PARKING 22", "NOVA PHARMACY #12",
               "TST* Willow Bistro", "APEX FITNESS CLUB", "GRANITE CITY ELECTRIC", "TIDAL CAR WASH", "LUMEN OPTICAL"]


def card_panel(n_firms=100, quarters=24, launch=12, partner_change=16, seed=0):
    """Population: six cells (age x region) with known shares. Firm i's true sales in quarter q are
    sum_c pop_c * s_icq, where s_icq (spend per person) has a firm trend, seasonality, firm shocks and cell-specific
    shocks. The panel holds n_cq panelists per cell: tilted young, drifting younger, and after `partner_change` drawn
    from a partner whose customers are older and mostly in region 1. Each cell's panel spend is n_cq * s_icq times
    sampling noise. History before `launch` is delivered at `launch`, built by the vendor with hindsight (shrunk halfway
    towards the reported sales); later quarters are delivered one quarter after they end."""
    rng = np.random.default_rng(seed)
    pop = np.array([[0.14, 0.16], [0.18, 0.17], [0.17, 0.18]])        # age x region shares of the population
    names = [f"{_STEMS[i % 40]} {_KIND[(i // 40 + i) % 5]}" for i in range(n_firms)]   # stems shared by up to 3
    tilt = rng.lognormal(0.0, 0.6, (n_firms, 3, 2))                    # firm i's customers by cell
    trend = rng.normal(0.01, 0.01, n_firms)
    cell_trend = rng.normal(0.0, 0.01, (n_firms, 3, 2))               # some firms gain young customers, some old
    season = np.array([0.0, 0.03, 0.0, 0.12])
    s = np.zeros((n_firms, quarters, 3, 2))
    level = np.zeros(n_firms)
    for q in range(quarters):
        level += trend + 0.02 * rng.standard_normal(n_firms)
        cell = np.log(tilt) + (q * cell_trend) + 0.01 * rng.standard_normal((n_firms, 3, 2))
        s[:, q] = 100.0 * np.exp(level[:, None, None] + cell + season[q % 4])
    sales = np.einsum("iqar,ar->iq", s, pop)
    n = np.zeros((quarters, 3, 2))
    for q in range(quarters):
        if q < partner_change:
            young = 0.45 + 0.01 * q                                    # the tilt drifts younger
            ages = np.array([young, (1 - young) * 0.6, (1 - young) * 0.4])
            n[q] = 50000 * ages[:, None] * np.array([0.5, 0.5])[None, :]
        else:
            ages = np.array([0.15, 0.35, 0.5])
            n[q] = 30000 * ages[:, None] * np.array([0.25, 0.75])[None, :]
    panel = n[None] * s * np.exp(rng.normal(0.0, 1.0, s.shape) / np.sqrt(n[None] / 2.0))
    return {"names": names, "sales": sales, "spend": s, "panel": panel, "panelists": n, "pop": pop,
            "launch": launch, "partner_change": partner_change,
            "strings": {i: _strings(rng, names[i]) for i in range(n_firms)}, "distractors": DISTRACTORS}
