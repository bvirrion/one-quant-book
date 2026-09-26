"""Numbers gate: every numerical answer printed in Book 12, chapter 13 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_text as m  # noqa: E402
from firm_textml import EVENTS, extract_event, ngrams, tokenize  # noqa: E402


def test_corpus():
    c = m.corpus()
    tr, te = m.split()
    assert (len(c["docs"]), len(tr), len(te), len(c["companies"]), len(EVENTS)) == (20000, 11923, 8077, 32, 19)
    assert len(c["sm"].reused()) == 4
    assert sum(1 for x in c["companies"] if x["name"].startswith("Apex")) == 3
    assert (len(m.POS), len(m.NEG)) == (11, 16)
    assert m.n_features() == {(1, 1): 123, (1, 2): 473}
    assert round(100 * m.compound_share()) == 9


def test_tokens():
    t = tokenize("<co> beat estimates but cut guidance amid copper demand")
    assert t == ["<co>", "beat", "estimates", "but", "cut", "guidance", "amid", "copper", "demand"]
    assert ngrams(t)[:5] == ["<co> beat", "beat estimates", "estimates but", "but cut", "cut guidance"]
    assert len(ngrams(t)) == 8
    assert ngrams(tokenize("<co> did not cut guidance")) == ["<co> did", "did not", "not cut", "cut guidance"]


def test_scores():
    s = {k: round(v, 3) for k, v in m.scores().items()}
    assert s == {"dictionary": 0.224, "tf-idf unigrams": 0.273, "tf-idf n-grams": 0.257, "supervised words": 0.238,
                 "embeddings": 0.094, "event rules": 0.292, "truth": 0.295}


def test_learning_curve():
    lc = m.learning_curve()
    assert lc[300]["supervised words"] == 0.0
    for n in (300, 1000):
        assert max(lc[n]["tf-idf unigrams"], lc[n]["tf-idf n-grams"], lc[n]["supervised words"]) < lc[n]["dictionary"]
    assert lc[3000]["tf-idf unigrams"] > lc[3000]["dictionary"]
    assert max(lc[3000]["tf-idf n-grams"], lc[3000]["supervised words"]) < lc[3000]["dictionary"]
    assert min(lc[10000]["tf-idf n-grams"], lc[10000]["supervised words"]) > lc[10000]["dictionary"]


def test_dictionary_cases():
    d = {k: (round(a, 2), b) for k, (a, b) in m.dictionary_cases().items()}
    assert d["beat"] == (0.20, 1.0) and d["cut"] == (-0.18, -1.5)
    assert d["beat_cut"] == (0.0, -1.2) and d["award"][0] > 0 and d["award"][1] == 0.0
    assert d["not_cut"][0] < 0 and d["not_cut"][1] == 0.3 and d["buyback"] == (0.0, 0.7)
    assert round((1 - 1) / 6, 2) == 0.0 and 1 / 4 == 0.25


def test_supervised_list():
    w = m.supervised_list()
    assert len(w) == 41
    lo = min(w, key=w.get)
    assert (lo, round(w[lo], 2), round(w["takeover"], 2)) == ("trims", -1.43, 1.79)
    assert w["takeover"] == max(w.values())                              # tied with "agrees", same headlines
    assert sorted(w, key=w.get)[1] == "halves" and "to" in w and "be" in w


def test_topics():
    top, purity = m.topics()
    assert top[0] == ["analysts", "fell", "short", "expectations", "forecasts", "exceeded"]
    assert top[4] == ["wins", "authorises", "program", "repurchase", "industry", "award"]
    assert len(top) == 6 and round(100 * sum(purity.values()) / len(purity)) == 63


def test_events_and_ner():
    assert m.extraction_accuracy() == 1.0 and m.ner_recall() == 1.0
    assert extract_event(tokenize("<co> surpasses consensus")) == ("neutral", 0.0)
    assert extract_event(tokenize("<co> did not lower full-year forecast"))[0] == "not_cut"


def test_embeddings():
    p = {(a, b): round(c, 2) for a, b, _, c in m.pairs()}
    assert min(p[("beat", "tops")], p[("raised", "lifts")], p[("guidance", "outlook")]) > 0.99
    assert p[("beat", "missed")] == 0.95


def test_linking():
    lk = {k: {w: tuple(round(100 * x, 1) for x in v) for w, v in r.items()} for k, r in m.linking().items()}
    assert lk["name"] == {"point in time": (100.0, 100.0, 100.0), "today": (89.3, 89.3, 100.0)}
    assert lk["short"] == {"point in time": (98.2, 100.0, 98.2), "today": (86.8, 88.6, 98.0)}
    assert lk["ticker"] == {"point in time": (100.0, 100.0, 100.0), "today": (84.5, 92.4, 91.5)}
    assert lk["all"] == {"point in time": (99.5, 100.0, 99.5), "today": (87.5, 89.7, 97.5)}
    a = m.apex()
    assert (a[True], round(100 * a[False][0], 1), a[False][1]) == ((1.0, 737), 58.0, 245)


def test_exercises():
    assert (round(math.log(20000 / 3000), 2), round(math.log(20000 / 200), 2)) == (1.90, 4.61)
    assert round(math.log(100) / math.log(20000 / 3000), 1) == 2.4
    u = m.unmasked()
    assert (round(u["tf-idf words"], 3), round(u["supervised words"], 3)) == (0.266, 0.238)
    assert u["company words kept by the screen"] == []
    # exercise 8: the two compounds need contradictory values of w_but - b
    assert (round(-1.2 - (1.0 - 1.5), 1), round(1.2 - (-1.0 + 1.5), 1)) == (-0.7, 0.7)
