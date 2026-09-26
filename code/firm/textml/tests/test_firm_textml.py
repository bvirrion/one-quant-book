import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_textml import (  # noqa: E402
    AliasTable,
    dictionary_score,
    doc_vectors,
    extract_event,
    link,
    news_corpus,
    ngrams,
    ppmi_svd,
    recognise,
    supervised_score,
    supervised_words,
    tokenize,
)

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "secmaster"))
from firm_secmaster import SecurityMaster  # noqa: E402


def test_tokens_and_ngrams():
    t = tokenize("ACME Corp. beat estimates, didn't cut <co>!")
    assert t == ["acme", "corp", "beat", "estimates", "didn't", "cut", "<co>"]
    assert ngrams(["a", "b", "c"], 2) == ["a b", "b c"] and ngrams(["a", "b", "c"], 3) == ["a b c"]
    assert dictionary_score(["good", "bad", "bad", "x"], {"good"}, {"bad"}) == -0.25


def test_supervised_screen_finds_a_planted_word():
    rng = np.random.default_rng(0)
    docs, rets = [], []
    for _ in range(4000):
        toks = [f"w{rng.integers(20)}", f"w{rng.integers(20)}"]
        r = rng.standard_normal()
        if rng.random() < 0.1:
            toks.append("good")
            r += 1.0
        docs.append(toks)
        rets.append(r)
    w = supervised_words(docs, rets, min_count=30, z=4.0)
    assert set(w) == {"good"} and 0.8 < w["good"] < 1.3
    assert supervised_score(["good", "w1"], w) == w["good"] and supervised_score(["w1"], w) == 0.0


def test_embeddings_group_identical_contexts():
    docs = [["x", "a", "ctx1"], ["x", "b", "ctx1"], ["y", "c", "ctx2"], ["y", "d", "ctx2"]] * 50
    vocab, V = ppmi_svd(docs, k=3, min_count=5)
    v = {w: V[vocab.index(w)] for w in vocab}
    assert v["a"] @ v["b"] > 0.99 and abs(v["a"] @ v["c"]) < 0.2
    assert doc_vectors([["a", "zzz"]], vocab, V).shape == (1, 3)


def test_event_rules():
    assert extract_event(tokenize("<co> tops forecasts but lowers outlook"))[0] == "beat_cut"
    assert extract_event(tokenize("<co> fell short of estimates but boosts guidance"))[0] == "miss_raise"
    assert extract_event(tokenize("<co> did not trim outlook"))[0] == "not_cut"
    assert extract_event(tokenize("<co> wins industry award"))[0] == "award"
    assert extract_event(tokenize("<co> holds annual meeting")) == ("neutral", 0.0)


def test_point_in_time_linking():
    sm, tab = SecurityMaster(), AliasTable()
    sm.list(1, "OLD", 0)
    sm.rename(1, "NEW", 100)
    sm.list(2, "ABC", 0)
    sm.delist(2, 150, "merger")
    sm.list(3, "ABC", 200)
    tab.add(1, "Alpha Mining", "name", 0, 120)
    tab.add(1, "Beta Mining", "name", 120)
    tab.add(1, "Apex", "short", 0)
    tab.add(4, "Apex", "short", 0)
    sectors = {1: ["ore"], 4: ["patients"], 2: [], 3: []}
    args = (tab, sm, sectors, {4: 10, 1: 1})
    assert link("OLD", 50, [], *args) == 1 and link("OLD", 300, [], *args) is None
    assert link("ABC", 50, [], *args) == 2 and link("ABC", 300, [], *args) == 3
    assert link("Alpha Mining", 50, [], *args) == 1 and link("Alpha Mining", 300, [], *args) is None
    assert link("Apex", 50, ["ore"], *args) == 1 and link("Apex", 50, [], *args) == 4
    assert recognise("Apex Mining beat; APX fell", ["Apex", "Apex Mining", "APX"]) == [(0, 11, "Apex Mining"),
                                                                                      (18, 21, "APX")]


def test_corpus_is_consistent():
    c = news_corpus(2000, seed=1)
    sm = c["sm"]
    for d in c["docs"][:500]:
        if d["kind"] == "ticker":
            assert sm.resolve(d["surface"], d["date"]) == d["pid"]
        assert d["text"].startswith(d["surface"])
    assert len(sm.reused()) == 4
