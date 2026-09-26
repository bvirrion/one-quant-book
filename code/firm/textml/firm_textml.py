"""firm.textml -- text to numbers, and mentions to securities (Book 12, chapter 13).

A synthetic news corpus with a known truth (companies with shared short names, ticker changes and reuse, renames;
headlines built from event phrases with compound clauses and negations; a reaction return per headline), and the
tools that turn text into forecasts: a tokeniser, n-grams, dictionary scores, a return-supervised word list, word
embeddings from the singular value decomposition of a co-occurrence matrix, a small topic model, a rule-based event
extractor, a gazetteer named-entity recogniser, and a point-in-time entity linker on the security master's tickers.

API (stable):
    tokenize(text) -> lowercase tokens         ngrams(tokens, n) -> ["w1 w2", ...]
    dictionary_score(tokens, pos, neg)         (positive - negative hits) / tokens
    supervised_words(docs, returns, min_count, z) -> {word: weight}   words whose presence moves the mean return
    supervised_score(tokens, weights)          mean weight of the selected words present (0 if none)
    ppmi_svd(docs, k, min_count) -> (vocab, vectors)                 word embeddings (unit rows)
    doc_vectors(docs, vocab, vectors) -> array                        mean of the words' vectors
    EVENTS, extract_event(tokens) -> (event, effect)                  rule-based event extraction
    AliasTable: .add(pid, alias, kind, start, end) .valid(alias, date) .aliases() (names and short names in time)
    recognise(text, gazetteer) -> [(start, end, surface)]             longest-match gazetteer NER
    link(surface, date, context, table, sm, sectors, prior) -> pid or None
    news_corpus(n_docs, seed, days) -> dict(docs, table, sm, companies, sectors)
"""
from __future__ import annotations

import pathlib
import re
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "secmaster"))
from firm_secmaster import SecurityMaster  # noqa: E402

_TOKEN = re.compile(r"<co>|[a-z0-9]+(?:'[a-z]+)?")


def tokenize(text):
    return _TOKEN.findall(text.lower())


def ngrams(tokens, n=2):
    return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def dictionary_score(tokens, pos, neg):
    if not tokens:
        return 0.0
    return (sum(t in pos for t in tokens) - sum(t in neg for t in tokens)) / len(tokens)


def supervised_words(docs, returns, min_count=30, z=3.0):
    """Keep the words whose documents' mean return differs from the rest's by more than z standard errors; each
    word's weight is that difference (the return-supervised screen, in the spirit of Ke, Kelly and Xiu)."""
    r = np.asarray(returns, dtype=float)
    where = defaultdict(list)
    for i, toks in enumerate(docs):
        for w in set(toks):
            where[w].append(i)
    sd, n, tot = r.std(), len(r), r.sum()
    out = {}
    for w, idx in where.items():
        k = len(idx)
        if k < min_count or k > n - min_count:
            continue
        m_in = r[idx].mean()
        m_out = (tot - r[idx].sum()) / (n - k)
        se = sd * np.sqrt(1 / k + 1 / (n - k))
        if abs(m_in - m_out) > z * se:
            out[w] = float(m_in - m_out)
    return out


def supervised_score(tokens, weights):
    hits = [weights[t] for t in set(tokens) if t in weights]
    return float(np.mean(hits)) if hits else 0.0


def ppmi_svd(docs, k=16, min_count=20):
    """Word vectors: positive pointwise mutual information of words co-occurring in a document, reduced by a
    truncated singular value decomposition; rows scaled to unit length."""
    cnt = Counter(t for d in docs for t in set(d))
    vocab = sorted(w for w, c in cnt.items() if c >= min_count)
    ix = {w: i for i, w in enumerate(vocab)}
    C = np.zeros((len(vocab), len(vocab)))
    for d in docs:
        ids = sorted({ix[t] for t in d if t in ix})
        for a in ids:
            for b in ids:
                if a != b:
                    C[a, b] += 1.0
    tot = C.sum()
    row = C.sum(1, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        pmi = np.log(C * tot / (row @ row.T))
    M = np.where(np.isfinite(pmi) & (pmi > 0), pmi, 0.0)
    U, S, _ = np.linalg.svd(M)
    V = U[:, :k] * np.sqrt(S[:k])
    V /= np.linalg.norm(V, axis=1, keepdims=True) + 1e-12
    return vocab, V


def doc_vectors(docs, vocab, vectors):
    ix = {w: i for i, w in enumerate(vocab)}
    out = np.zeros((len(docs), vectors.shape[1]))
    for j, d in enumerate(docs):
        ids = [ix[t] for t in d if t in ix]
        if ids:
            out[j] = vectors[ids].mean(0)
    return out


# ------------------------------------------------------------------------------------------------ the corpus
# event: (phrases, effect on the reaction return in %); verbs and objects are crossed so that synonyms share contexts
_BEAT, _MISS = ["beat", "tops", "exceeded"], ["missed", "fell short of", "disappointed"]
_TGT = ["estimates", "forecasts", "expectations"]
_UP, _DOWN, _BASE = ["raised", "lifts", "boosts"], ["cut", "lowers", "trims"], ["cut", "lower", "trim"]
_GUIDE = ["guidance", "outlook", "full-year forecast"]


def _cross(*parts):
    out = [""]
    for part in parts:
        out = [f"{a} {b}".strip() for a in out for b in part]
    return out


EVENTS = {
    "beat": (_cross(_BEAT, _TGT), 1.0),
    "miss": (_cross(_MISS, _TGT), -1.0),
    "raise": (_cross(_UP, _GUIDE), 1.5),
    "cut": (_cross(_DOWN, _GUIDE), -1.5),
    "beat_cut": (_cross(_BEAT, _TGT, ["but"], _DOWN, _GUIDE), -1.2),
    "miss_raise": (_cross(_MISS, _TGT, ["but"], _UP, _GUIDE), 1.2),
    "not_cut": (_cross(["did not"], _BASE, _GUIDE), 0.3),
    "recall": (["announces product recall", "recalls products"], -1.0),
    "lawsuit": (["faces lawsuit", "sued by investors"], -0.7),
    "investigation": (["under regulatory investigation", "receives subpoena"], -0.9),
    "win": (["wins major contract", "awarded contract"], 0.8),
    "award": (["wins industry award", "wins design prize"], 0.0),
    "upgrade": (["upgraded by analysts", "gets rating upgrade"], 0.8),
    "downgrade": (["downgraded by analysts", "gets rating downgrade"], -0.8),
    "buyback": (["announces share buyback", "authorises repurchase program"], 0.7),
    "dividend_cut": (["suspends dividend", "halves dividend"], -1.2),
    "merger": (["to be acquired at premium", "agrees to takeover"], 2.0),
    "ceo": (["chief executive resigns", "ceo steps down"], -0.5),
    "neutral": (["files annual report citing tax liability", "reports capital costs in line",
                 "schedules earnings call", "announces debt refinancing", "holds annual meeting",
                 "reports record attendance at annual meeting"], 0.0),
}
EVENT_P = {"neutral": 0.22, "award": 0.04, "beat": 0.07, "miss": 0.07, "raise": 0.05, "cut": 0.05, "beat_cut": 0.05,
           "miss_raise": 0.04, "not_cut": 0.04, "recall": 0.03, "lawsuit": 0.04, "investigation": 0.03, "win": 0.04,
           "upgrade": 0.04, "downgrade": 0.04, "buyback": 0.04, "dividend_cut": 0.03, "merger": 0.02, "ceo": 0.02}
_KEYS = {"beat": ("beat", "tops", "exceeded"), "miss": ("missed", "short", "disappointed"),
         "raise": ("raised", "lifts", "boosts"), "cut": ("cut", "lowers", "trims", "lower", "trim"),
         "recall": ("recall", "recalls"), "lawsuit": ("lawsuit", "sued"),
         "investigation": ("investigation", "subpoena"),
         "win": ("contract",), "award": ("award", "prize"), "upgrade": ("upgraded", "upgrade"),
         "downgrade": ("downgraded", "downgrade"), "buyback": ("buyback", "repurchase"),
         "dividend_cut": ("suspends", "halves"), "merger": ("acquired", "takeover"), "ceo": ("resigns", "steps")}


def extract_event(tokens):
    """Rule-based event extraction: find the event keywords; 'not' before a guidance cut turns it into 'not_cut';
    a result and a guidance change joined by 'but' is a compound event."""
    t = set(tokens)
    found = {e for e, ks in _KEYS.items() if t & set(ks)}
    if "not" in t and "cut" in found:
        return "not_cut", EVENTS["not_cut"][1]
    if "but" in t and found >= {"beat", "cut"}:
        return "beat_cut", EVENTS["beat_cut"][1]
    if "but" in t and found >= {"miss", "raise"}:
        return "miss_raise", EVENTS["miss_raise"][1]
    if len(found) == 1:
        e = found.pop()
        return e, EVENTS[e][1]
    return "neutral", 0.0


class AliasTable:
    """Names and short names of companies, each valid from `start` to `end` (exclusive; None = still valid)."""

    def __init__(self):
        self.rows = []

    def add(self, pid, alias, kind, start, end=None):
        self.rows.append((alias, kind, pid, start, end))

    def valid(self, alias, date):
        return [(kind, pid) for a, kind, pid, s, e in self.rows if a == alias and s <= date and (e is None or date < e)]

    def aliases(self):
        return sorted({a for a, *_ in self.rows})


def recognise(text, gazetteer):
    """Longest-match named-entity recognition on a gazetteer of surfaces (names, short names, tickers)."""
    out, i = [], 0
    by_len = sorted(gazetteer, key=len, reverse=True)
    while i < len(text):
        hit = next((g for g in by_len if text.startswith(g, i) and (i + len(g) == len(text)
                                                                    or not text[i + len(g)].isalnum())
                    and (i == 0 or not text[i - 1].isalnum())), None)
        if hit:
            out.append((i, i + len(hit), hit))
            i += len(hit)
        else:
            i += 1
    return out


def link(surface, date, context, table, sm, sectors, prior):
    """Map a recognised surface to a permanent id as of `date`: a ticker through the security master, a name or a
    short name through the alias table; several candidates are separated by sector words in the context, then by
    the prior (the candidate with most past coverage)."""
    if surface.isupper():
        return sm.resolve(surface, date)
    cands = sorted({pid for _, pid in table.valid(surface, date)})
    if len(cands) > 1:
        ctx = set(context)
        by_sector = [p for p in cands if ctx & set(sectors[p])]
        cands = by_sector if len(by_sector) == 1 else sorted(cands, key=lambda p: -prior.get(p, 0))
    return cands[0] if cands else None


SECTOR_WORDS = {"software": ["cloud", "subscribers", "platform"], "mining": ["copper", "ore", "gold"],
                "health": ["patients", "drug", "clinic"], "bank": ["loans", "deposits", "lending"],
                "retail": ["stores", "shoppers", "malls"], "energy": ["oil", "gas", "drilling"]}
_FIRST = ["Borealis", "Cobalt", "Delta", "Ember", "Fulcrum", "Granite", "Harbor", "Ionic", "Juniper", "Keystone",
          "Lumen", "Meridian", "Nimbus", "Orion", "Pinnacle", "Quartz", "Redwood", "Summit", "Tidal", "Umbra",
          "Vertex", "Willow", "Xenon", "Yarrow", "Zephyr"]
_CTX = ["", " amid {w} demand", " as {w} volumes shift", " in {w} update"]


def news_corpus(n_docs=20000, seed=0, days=1512):
    """28 companies (three called Apex) plus 4 later listings that reuse delisted tickers; 6 ticker changes and 3
    renames; one headline per document: '<mention> <event phrase><context>' with a reaction return in % equal to the
    event's effect plus noise of standard deviation 3."""
    rng = np.random.default_rng(seed)
    sm, table = SecurityMaster(), AliasTable()
    sectors, companies = {}, []
    secs = list(SECTOR_WORDS)
    names = [("Apex Software", "APX", "software"), ("Apex Mining", "APXM", "mining"), ("Apex Health", "APH", "health")]
    names += [(f"{f} {secs[i % 6].capitalize()}", f[:3].upper(), secs[i % 6]) for i, f in enumerate(_FIRST)]
    for pid, (name, tick, sec) in enumerate(names):
        sm.list(pid, tick, 0)
        table.add(pid, name, "name", 0)
        table.add(pid, name.split()[0], "short", 0)
        sectors[pid] = SECTOR_WORDS[sec]
        companies.append({"pid": pid, "name": name, "sector": sec, "start": 0, "end": None})
    for pid in (3, 5, 7, 9, 11, 13):                                     # ticker changes
        d = int(rng.integers(200, days - 200))
        sm.rename(pid, sm.ticker(pid, 0) + "X", d)
    for pid, new in ((4, "Northwind"), (8, "Aurora"), (12, "Crestline")):   # renames: the old names stop
        d = int(rng.integers(300, days - 300))
        old = companies[pid]["name"]
        table.rows = [r if not (r[2] == pid and r[3] == 0) else (*r[:4], d) for r in table.rows]
        table.add(pid, f"{new} {old.split()[1]}", "name", d)
        table.add(pid, new, "short", d)
    for j, pid in enumerate((15, 18, 21, 24)):                          # delisted, ticker reused 30 days later
        d = int(rng.integers(500, days - 400))
        tick = sm.ticker(pid, d)
        sm.delist(pid, d, "merger")
        companies[pid]["end"] = d
        table.rows = [r if not (r[2] == pid and r[4] is None) else (*r[:4], d + 1) for r in table.rows]
        new = len(companies)
        name = f"Nova {secs[j].capitalize()} {j + 1}"
        sm.list(new, tick, d + 30)
        table.add(new, name, "name", d + 30)
        sectors[new] = SECTOR_WORDS[secs[j]]
        companies.append({"pid": new, "name": name, "sector": secs[j], "start": d + 30, "end": None})
    cover = np.array([3.0, 1.0, 1.0] + [1.0] * (len(companies) - 3))    # Apex Software is the most covered
    ev_names, ev_p = list(EVENT_P), np.array(list(EVENT_P.values()))
    docs = []
    for _ in range(n_docs):
        date = int(rng.integers(0, days))
        live = [c["pid"] for c in companies if c["start"] <= date and (c["end"] is None or date <= c["end"])]
        w = cover[live] / cover[live].sum()
        pid = int(rng.choice(live, p=w))
        ev = ev_names[rng.choice(len(ev_names), p=ev_p / ev_p.sum())]
        phrase = EVENTS[ev][0][rng.integers(len(EVENTS[ev][0]))]
        kind = rng.choice(["name", "short", "ticker"], p=[0.5, 0.3, 0.2])
        valid = [a for a, k, p, s, e in table.rows if p == pid and k == kind and s <= date and (e is None or date < e)]
        if kind == "ticker" or not valid:
            kind, surface = "ticker", sm.ticker(pid, date)
        else:
            surface = valid[0]
        ctx = _CTX[rng.integers(len(_CTX))].format(w=sectors[pid][rng.integers(3)])
        eff = EVENTS[ev][1]
        docs.append({"date": date, "pid": pid, "text": f"{surface} {phrase}{ctx}", "event": ev, "effect": eff,
                     "ret": eff + 3.0 * rng.standard_normal(), "kind": str(kind), "surface": surface})
    return {"docs": docs, "table": table, "sm": sm, "companies": companies, "sectors": sectors}
