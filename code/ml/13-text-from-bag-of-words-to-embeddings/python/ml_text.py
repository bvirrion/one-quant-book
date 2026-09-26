"""Text from bag of words to embeddings (One Quant Book 12, chapter 13).

A synthetic corpus of 20,000 headlines over six years (firm.textml.news_corpus): the first 60% of the days train, the
rest test. Mentions are recognised and masked, then five scores are compared by their rank information coefficient
with the reaction return: a hand-built dictionary, tf-idf n-grams with a regularised logistic regression, a
return-supervised word list, word embeddings from a co-occurrence matrix with a ridge regression on document vectors,
and rule-based event extraction. Entity linking is scored with point-in-time aliases and with today's."""
from __future__ import annotations

import functools
import os
import pathlib
import sys

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "textml"))
from firm_textml import (  # noqa: E402
    dictionary_score,
    doc_vectors,
    extract_event,
    link,
    news_corpus,
    ppmi_svd,
    recognise,
    supervised_score,
    supervised_words,
    tokenize,
)

DAYS, SPLIT = 1512, 907
POS = {"beat", "tops", "exceeded", "raised", "lifts", "boosts", "wins", "awarded", "upgraded", "upgrade", "premium"}
NEG = {"missed", "short", "disappointed", "cut", "lowers", "trims", "lower", "recall", "recalls", "lawsuit", "sued",
       "downgraded", "downgrade", "resigns", "investigation", "suspends"}
SIZES = (300, 1000, 3000, 10000)


@functools.lru_cache(maxsize=1)
def corpus():
    c = news_corpus(20000, 0, DAYS)
    gaz = set(c["table"].aliases()) | {t for sp in (c["sm"].spans(p["pid"]) for p in c["companies"]) for *_, t in sp}
    for d in c["docs"]:
        spans = recognise(d["text"], gaz)
        d["found"] = spans
        masked, last = [], 0
        for a, b, _ in spans:
            masked.append(d["text"][last:a] + "<co>")
            last = b
        d["masked"] = "".join(masked) + d["text"][last:]
        d["tokens"] = tokenize(d["masked"])
    return c


def split():
    docs = corpus()["docs"]
    tr = [d for d in docs if d["date"] < SPLIT]
    te = [d for d in docs if d["date"] >= SPLIT]
    return tr, te


def ic(score, docs):
    """Rank information coefficient; 0 for a constant score (nothing selected)."""
    if np.ptp(np.asarray(score, dtype=float)) == 0:
        return 0.0
    return float(spearmanr(score, [d["ret"] for d in docs])[0])


def _tfidf_lr(tr, te, ngram=(1, 2)):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression

    vec = TfidfVectorizer(tokenizer=tokenize, lowercase=False, token_pattern=None, ngram_range=ngram, min_df=3)
    Xtr = vec.fit_transform([d["masked"] for d in tr])
    lr = LogisticRegression(C=1.0, max_iter=2000).fit(Xtr, [d["ret"] > 0 for d in tr])
    return lr.decision_function(vec.transform([d["masked"] for d in te]))


def _embed(tr, te, k=16):
    from sklearn.linear_model import Ridge

    vocab, V = ppmi_svd([d["tokens"] for d in tr], k, min_count=10)
    Dtr, Dte = doc_vectors([d["tokens"] for d in tr], vocab, V), doc_vectors([d["tokens"] for d in te], vocab, V)
    return Ridge(alpha=1.0).fit(Dtr, [d["ret"] for d in tr]).predict(Dte)


def _events(tr, te):
    means = {}
    for d in tr:
        means.setdefault(extract_event(d["tokens"])[0], []).append(d["ret"])
    means = {e: float(np.mean(v)) for e, v in means.items()}
    return [means.get(extract_event(d["tokens"])[0], 0.0) for d in te]


def scores(n_train=None):
    tr, te = split()
    if n_train:
        tr = tr[:n_train]
    w = supervised_words([d["tokens"] for d in tr], [d["ret"] for d in tr], min_count=max(10, len(tr) // 300))
    return {"dictionary": ic([dictionary_score(d["tokens"], POS, NEG) for d in te], te),
            "tf-idf unigrams": ic(_tfidf_lr(tr, te, (1, 1)), te),
            "tf-idf n-grams": ic(_tfidf_lr(tr, te), te),
            "supervised words": ic([supervised_score(d["tokens"], w) for d in te], te),
            "embeddings": ic(_embed(tr, te), te),
            "event rules": ic(_events(tr, te), te),
            "truth": ic([d["effect"] for d in te], te)}


@functools.lru_cache(maxsize=1)
def learning_curve():
    return {n: scores(n) for n in SIZES}


def dictionary_cases():
    """Mean dictionary score on the test half and the planted effect, for events a dictionary misreads."""
    _, te = split()
    out = {}
    for ev in ("beat", "cut", "beat_cut", "not_cut", "award", "buyback", "neutral"):
        ds = [d for d in te if d["event"] == ev]
        out[ev] = (float(np.mean([dictionary_score(d["tokens"], POS, NEG) for d in ds])), ds[0]["effect"])
    return out


def supervised_list():
    tr, _ = split()
    return supervised_words([d["tokens"] for d in tr], [d["ret"] for d in tr], min_count=40)


@functools.lru_cache(maxsize=1)
def embedding():
    tr, _ = split()
    return ppmi_svd([d["tokens"] for d in tr], 16, min_count=10)


def cosine(a, b):
    vocab, V = embedding()
    return float(V[vocab.index(a)] @ V[vocab.index(b)])


def extraction_accuracy():
    docs = corpus()["docs"]
    return float(np.mean([extract_event(d["tokens"])[0] == d["event"] for d in docs]))


def ner_recall():
    docs = corpus()["docs"]
    return float(np.mean([len(d["found"]) == 1 and d["found"][0][2] == d["surface"] for d in docs]))


@functools.lru_cache(maxsize=1)
def linking():
    """Share of mentions linked to the right permanent id, by mention kind, with aliases as of the headline's date
    (point in time) and as of the last day (today's table)."""
    c = corpus()
    tr, te = split()
    prior = {}
    for d in tr:
        prior[d["pid"]] = prior.get(d["pid"], 0) + 1
    out = {}
    for kind in ("name", "short", "ticker", "all"):
        ds = [d for d in c["docs"] if kind in ("all", d["kind"])]
        row = {}
        for when, date in (("point in time", None), ("today", DAYS - 1)):
            got = [link(d["surface"], d["date"] if date is None else date, d["tokens"], c["table"], c["sm"],
                        c["sectors"], prior) for d in ds]
            linked = [g for g in got if g is not None]
            row[when] = (float(np.mean([g == d["pid"] for g, d in zip(got, ds, strict=True)])),
                         len(linked) / len(ds),
                         float(np.mean([g == d["pid"] for g, d in zip(got, ds, strict=True) if g is not None])))
        out[kind] = row
    return out


def apex():
    """Accuracy on the short name Apex, with and without a sector word in the headline."""
    c = corpus()
    tr, _ = split()
    prior = {}
    for d in tr:
        prior[d["pid"]] = prior.get(d["pid"], 0) + 1
    out = {}
    for has in (True, False):
        ds = [d for d in c["docs"] if d["surface"] == "Apex" and (len(d["tokens"]) > 0)
              and (any(t in w for w in c["sectors"].values() for t in d["tokens"]) == has)]
        out[has] = (float(np.mean([link("Apex", d["date"], d["tokens"], c["table"], c["sm"], c["sectors"], prior)
                                   == d["pid"] for d in ds])), len(ds))
    return out


def topics(k=6, seed=0):
    from sklearn.decomposition import LatentDirichletAllocation
    from sklearn.feature_extraction.text import CountVectorizer

    tr, _ = split()
    stop = ["<co>", "amid", "as", "in", "of", "by", "at", "and", "to", "demand", "volumes", "shift", "update"]
    vec = CountVectorizer(tokenizer=tokenize, lowercase=False, token_pattern=None, stop_words=stop, min_df=5)
    X = vec.fit_transform([d["masked"] for d in tr])
    lda = LatentDirichletAllocation(k, learning_method="batch", max_iter=30, random_state=seed, n_jobs=1).fit(X)
    words = vec.get_feature_names_out()
    top = [[words[i] for i in np.argsort(-comp)[:6]] for comp in lda.components_]
    dom = lda.transform(X).argmax(1)
    ev = [d["event"] for d in tr]
    purity = {}
    for e in sorted(set(ev)):
        z = dom[[i for i, x in enumerate(ev) if x == e]]
        purity[e] = float(np.bincount(z, minlength=k).max() / len(z))
    return top, purity


PAIRS = (("beat", "tops", "same meaning"), ("raised", "lifts", "same meaning"), ("guidance", "outlook", "same meaning"),
         ("copper", "ore", "same sector"), ("oil", "gas", "same sector"), ("beat", "missed", "opposite"),
         ("tops", "disappointed", "opposite"), ("raised", "cut", "opposite"), ("lifts", "lowers", "opposite"),
         ("beat", "lawsuit", "unrelated"), ("raised", "copper", "unrelated"))


def pairs():
    return [(a, b, kind, cosine(a, b)) for a, b, kind in PAIRS]


def n_features():
    """Vocabulary sizes of the tf-idf representations (terms in at least 3 training headlines)."""
    from sklearn.feature_extraction.text import TfidfVectorizer

    tr, _ = split()
    out = {}
    for ng in ((1, 1), (1, 2)):
        vec = TfidfVectorizer(tokenizer=tokenize, lowercase=False, token_pattern=None, ngram_range=ng, min_df=3)
        out[ng] = vec.fit_transform([d["masked"] for d in tr]).shape[1]
    return out


def compound_share():
    return float(np.mean([d["event"] in ("beat_cut", "miss_raise") for d in corpus()["docs"]]))


def unmasked():
    """Exercise 7: the same models with the company mentions left in the text."""
    tr, te = split()
    tr_u = [dict(d, masked=d["text"], tokens=tokenize(d["text"])) for d in tr]
    te_u = [dict(d, masked=d["text"], tokens=tokenize(d["text"])) for d in te]
    w = supervised_words([d["tokens"] for d in tr_u], [d["ret"] for d in tr_u], min_count=40)
    names = {t for d in tr for t in tokenize(d["surface"])}
    return {"tf-idf words": ic(_tfidf_lr(tr_u, te_u, (1, 1)), te_u),
            "supervised words": ic([supervised_score(d["tokens"], w) for d in te_u], te_u),
            "company words kept by the screen": sorted(set(w) & names)}
