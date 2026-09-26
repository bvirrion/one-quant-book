"""Large language models in finance (One Quant Book 12, chapter 14).

Everything is local and small. (1) The model that knew: a tiny word-level transformer is trained as a language model
on the chapter-13 headlines, each followed by its outcome ("up" or "down"); the clean model's training data end at day
907, the contaminated model's at day 1,210. Both are scored on three periods, with and without names and dates
replaced by placeholders: the memorisation premium and the anonymisation test. (2) Retrieval over synthetic annual
filings: BM25, dense (co-occurrence embeddings), hybrid and embedding-expanded search, with questions whose wording
matches the filing's or not; a grounding check that abstains when the passage does not name the question's company and
year. (3) An agent that answers as-of questions through a tool registry, with and without the point-in-time guard."""
from __future__ import annotations

import functools
import os
import pathlib
import re
import sys

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402

_FIRM = pathlib.Path(__file__).resolve().parents[3] / "firm"
for _c in ("llmeval", "textml"):
    sys.path.insert(0, str(_FIRM / _c))
from firm_llmeval import (  # noqa: E402
    BM25,
    TinyLM,
    ToolRegistry,
    Vocab,
    dense_scores,
    expand_query,
    hybrid,
    next_logprobs,
    train_lm,
)
from firm_textml import doc_vectors, news_corpus, ppmi_svd, tokenize  # noqa: E402

N_DOCS, DAYS = 10000, 1512
CUT_CLEAN, CUT_CONTAM = 907, 1210
PERIODS = {"before both cut-offs": (0, CUT_CLEAN), "between the cut-offs": (CUT_CLEAN, CUT_CONTAM),
           "after both cut-offs": (CUT_CONTAM, DAYS)}
LM = {"d": 48, "heads": 4, "layers": 2, "max_len": 24}
TRAIN = {"epochs": 20, "lr": 3e-3, "batch": 64, "seed": 0}


@functools.lru_cache(maxsize=1)
def headlines():
    return news_corpus(N_DOCS, 0, DAYS)["docs"]


def sequence(d, anonymise=False):
    """'w<week> <mention tokens> <headline tokens> =>': the week and the company are the model's key to its memory."""
    ment = tokenize(d["surface"])
    body = tokenize(d["text"])[len(ment):]
    head = ["<date>", "<co>"] if anonymise else [f"w{d['date'] // 5}"] + ment
    return head + body + ["=>"]


def outcome(d):
    return "up" if d["ret"] > 0 else "down"


@functools.lru_cache(maxsize=1)
def vocab():
    docs = headlines()
    return Vocab([sequence(d) + ["up", "down"] for d in docs], specials=("<pad>", "<unk>", "<date>", "<co>"))


@functools.lru_cache(maxsize=2)
def model(cut):
    """A language model trained on every headline (and its outcome) published before `cut`; one in ten is
    anonymised so that the placeholders are known words."""
    V = vocab()
    rng = np.random.default_rng(0)
    seqs = [V.encode(sequence(d, rng.random() < 0.1) + [outcome(d)]) for d in headlines() if d["date"] < cut]
    m = TinyLM(len(V), **LM)
    losses = train_lm(m, seqs, **TRAIN)
    return m, losses


def accuracy(m, docs, anonymise=False):
    V = vocab()
    lp = next_logprobs(m, [V.encode(sequence(d, anonymise)) for d in docs])
    pred = lp[:, V.id("up")] > lp[:, V.id("down")]
    return float(np.mean(pred == np.array([d["ret"] > 0 for d in docs])))


def period(name):
    lo, hi = PERIODS[name]
    return [d for d in headlines() if lo <= d["date"] < hi]


@functools.lru_cache(maxsize=1)
def contamination():
    """Accuracy of each model on each period, with names and dates, and anonymised."""
    out = {}
    for label, cut in (("clean", CUT_CLEAN), ("contaminated", CUT_CONTAM)):
        m, _ = model(cut)
        out[label] = {p: (accuracy(m, period(p)), accuracy(m, period(p), True)) for p in PERIODS}
    return out


def planted_accuracy():
    """The skill ceiling after both cut-offs: the sign of the planted effect, right on the headlines with an effect
    and a coin (one half) on the others."""
    ds = period("after both cut-offs")
    hit = [(d["effect"] > 0) == (d["ret"] > 0) for d in ds if d["effect"] != 0]
    n0 = sum(d["effect"] == 0 for d in ds)
    return float(np.mean(hit)), len(hit), (sum(hit) + 0.5 * n0) / len(ds)


def verdict():
    c = contamination()
    b, a = "between the cut-offs", "after both cut-offs"
    return {k: {"premium": c[k][b][0] - c[k][a][0], "anonymisation loss": c[k][b][0] - c[k][b][1]} for k in c}


# ---------------------------------------------------------------------------------------------------- retrieval
METRICS = {"revenue": (["revenue", "sales", "turnover"], ["customers", "orders", "pricing", "demand"]),
           "debt": (["net debt", "borrowings", "leverage"], ["lenders", "interest", "bonds", "refinancing"]),
           "staff": (["headcount", "employees", "staff"], ["hiring", "offices", "salaries", "workforce"]),
           "capex": (["capital expenditure", "investment spending", "capex"], ["plants", "equipment", "machinery",
                                                                                 "construction"])}
YEARS = 5


def published(year):
    return 252 * (year + 1) + 50


@functools.lru_cache(maxsize=1)
def filings(seed=0):
    """One passage per company, fiscal year and metric: '<name> reported <synonym> of <value> million for year <y>, as
    <context words>'. Companies file only for the years they were listed for."""
    rng = np.random.default_rng(seed)
    comps = news_corpus(10, 0, DAYS)["companies"]
    out = []
    for c in comps:
        for y in range(YEARS):
            day = published(y)
            if day >= DAYS or c["start"] > 252 * y or (c["end"] is not None and c["end"] < day):
                continue
            for metric, (syns, ctx) in METRICS.items():
                syn = syns[rng.integers(3)]
                value = int(rng.integers(10, 1000))
                text = f"{c['name']} reported {syn} of {value} million for year {y}, as {ctx[0]} and {ctx[1]} changed"
                out.append({"pid": c["pid"], "name": c["name"], "year": y, "metric": metric, "syn": syn,
                            "value": value, "published": day, "text": text, "tokens": tokenize(text)})
    return out


def background(n=5000, seed=4):
    """General business sentences in which each metric's synonyms appear with that metric's context words: the
    stand-in for the large general corpus a real embedding model is trained on."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        syns, ctx = METRICS[list(METRICS)[rng.integers(4)]]
        words = tokenize(syns[rng.integers(3)]) + [ctx[i] for i in rng.choice(4, 2, replace=False)]
        words += [["rose", "fell", "held"][rng.integers(3)], ["company", "firm", "group"][rng.integers(3)]]
        out.append([words[i] for i in rng.permutation(len(words))])
    return out


@functools.lru_cache(maxsize=1)
def indexes():
    docs = filings()
    toks = [d["tokens"] for d in docs]
    vocab_, V = ppmi_svd(background(), k=8, min_count=5)
    return BM25(toks), vocab_, V, doc_vectors(toks, vocab_, V)


@functools.lru_cache(maxsize=1)
def questions(seed=1):
    """One question per passage, worded with a synonym drawn at random: about a third match the passage's word."""
    rng = np.random.default_rng(seed)
    docs = filings()
    qs = []
    for i, d in enumerate(docs):
        syn = METRICS[d["metric"]][0][rng.integers(3)]
        qs.append({"text": f"what was the {syn} of {d['name']} for year {d['year']}", "target": i,
                   "exact": syn == d["syn"], "value": d["value"]})
    return qs


def search(q_tokens, method, w=1.0):
    bm, vocab_, V, D = indexes()
    if method == "expanded":
        return bm.scores(expand_query(q_tokens, vocab_, V))
    s_b = bm.scores(q_tokens)
    if method == "bm25":
        return s_b
    s_d = dense_scores(D, doc_vectors([q_tokens], vocab_, V)[0])
    return s_d if method == "dense" else hybrid(s_b, s_d, w)


def answer(passage):
    m = re.search(r" of (\d+) million", passage["text"])
    return int(m.group(1)) if m else None


@functools.lru_cache(maxsize=1)
def retrieval():
    """Share of questions whose top passage is the right one, by method, for questions worded like the passage or
    not."""
    docs = filings()
    out = {}
    for method in ("bm25", "dense", "hybrid", "expanded"):
        hit = {True: [], False: []}
        for q in questions():
            top = int(np.argmax(search(tokenize(q["text"]), method)))
            hit[q["exact"]].append(answer(docs[top]) == q["value"] and top == q["target"])
        out[method] = {"same word": float(np.mean(hit[True])), "other word": float(np.mean(hit[False]))}
    return out


def grounded(q, passage):
    """Answer only if the passage names the question's company and year."""
    name, year = re.search(r"of (.+) for year (\d+)$", q).groups()
    return passage["name"].lower() == name.lower() and passage["year"] == int(year)


def unanswerable(n=300, seed=2):
    """Questions about company-years with no filing: share answered anyway, with and without the grounding check."""
    rng = np.random.default_rng(seed)
    docs = filings()
    have = {(d["name"], d["year"]) for d in docs}
    names = sorted({d["name"] for d in docs})
    qs = []
    while len(qs) < n:
        name, y = names[rng.integers(len(names))], int(rng.integers(YEARS + 1))
        if (name, y) not in have:
            syn = METRICS["revenue"][0][rng.integers(3)]
            qs.append(f"what was the {syn} of {name} for year {y}")
    tops = [docs[int(np.argmax(search(tokenize(q), "expanded")))] for q in qs]
    return {"answered without the check": 1.0, "answered with the check": float(np.mean([grounded(q, t) for q, t in
                                                                                         zip(qs, tops, strict=True)]))}


def check_cost():
    """Share of answerable questions the grounding check turns away (hybrid search)."""
    docs = filings()
    qs = questions()
    return float(np.mean([not grounded(q["text"], docs[int(np.argmax(search(tokenize(q["text"]), "expanded")))])
                          for q in qs]))


# ---------------------------------------------------------------------------------------------------- the agent
def agent_answer(name, metric, as_of, guard=True):
    """'As of day t, what was <metric> of <company> in its latest annual filing?' The agent searches, keeps the
    passages about the company and the metric, and answers from the latest fiscal year it finds."""
    docs = filings()
    reg = ToolRegistry(as_of)

    def search_tool(query, as_of=None, k=20):
        s = search(tokenize(query), "expanded")
        order = np.argsort(-s)
        hits = [docs[i] for i in order if as_of is None or docs[i]["published"] <= as_of]
        return hits[:k]

    reg.register("search", search_tool, dated=guard)
    q = f"{METRICS[metric][0][0]} of {name}"
    hits = reg.call("search", query=q) or []
    hits = [h for h in hits if h["name"] == name and h["metric"] == metric]
    if not hits:
        return None, reg.log
    best = max(hits, key=lambda h: h["year"])
    return best, reg.log


@functools.lru_cache(maxsize=1)
def agent_run(n=400, seed=3):
    """Share of as-of questions answered from a filing published after the as-of date, and share answered with the
    right (latest available) figure, with and without the point-in-time guard."""
    rng = np.random.default_rng(seed)
    docs = filings()
    names = sorted({d["name"] for d in docs})
    out = {}
    cases = [(names[rng.integers(len(names))], list(METRICS)[rng.integers(4)], int(rng.integers(302, DAYS)))
             for _ in range(n)]
    for guard in (True, False):
        future, right, calls = [], [], 0
        for name, metric, t in cases:
            best, log = agent_answer(name, metric, t, guard)
            calls += len(log)
            avail = [d for d in docs if d["name"] == name and d["metric"] == metric and d["published"] <= t]
            truth = max(avail, key=lambda d: d["year"])["value"] if avail else None
            future.append(best is not None and best["published"] > t)
            right.append((best["value"] if best else None) == truth)
        out["guarded" if guard else "unguarded"] = {"future": float(np.mean(future)), "right": float(np.mean(right)),
                                                     "logged calls": calls}
    return out
