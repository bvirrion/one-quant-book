"""Numbers gate: every numerical answer printed in Book 12, chapter 14 (text and solutions). Trains two small language
models (about a minute on one core)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_llm as m  # noqa: E402


def pct(x):
    return round(100 * x, 1)


def test_setup():
    assert {p: len(m.period(p)) for p in m.PERIODS} == {"before both cut-offs": 5972, "between the cut-offs": 2016,
                                                          "after both cut-offs": 2012}
    assert len(m.vocab()) == 505
    acc, n, ceiling = m.planted_accuracy()
    assert (pct(acc), n, pct(ceiling), 2012 - n) == (66.0, 1462, 61.6, 550)


def test_contamination():
    c = {k: {p: (pct(a), pct(b)) for p, (a, b) in v.items()} for k, v in m.contamination().items()}
    assert c["clean"] == {"before both cut-offs": (69.7, 57.7), "between the cut-offs": (56.2, 56.0),
                          "after both cut-offs": (56.3, 55.3)}
    assert c["contaminated"] == {"before both cut-offs": (65.4, 57.2), "between the cut-offs": (64.8, 57.0),
                                 "after both cut-offs": (59.2, 58.1)}
    v = {k: (pct(x["premium"]), pct(x["anonymisation loss"])) for k, x in m.verdict().items()}
    assert v == {"clean": (-0.1, 0.2), "contaminated": (5.6, 7.8)}
    assert sum(p.numel() for p in m.model(m.CUT_CLEAN)[0].parameters()) == 106681


def test_retrieval():
    r = {k: (pct(v["same word"]), pct(v["other word"])) for k, v in m.retrieval().items()}
    assert r == {"bm25": (100.0, 5.0), "dense": (0.0, 1.1), "hybrid": (100.0, 18.2), "expanded": (86.3, 89.1)}
    qs = m.questions()
    same = sum(q["exact"] for q in qs)
    right = round(r["expanded"][0] / 100 * same) + round(r["expanded"][1] / 100 * (len(qs) - same))
    assert (len(m.filings()), len(qs), len(qs) - right, pct(right / len(qs))) == (540, 540, 64, 88.1)
    bm, vocab, V, _ = m.indexes()
    sims = [float(V[vocab.index(a)] @ V[vocab.index(b)]) for a, b in (("sales", "revenue"), ("sales", "turnover"),
                                                                       ("revenue", "turnover"))]
    assert min(sims) > 0.99


def test_grounding_and_agent():
    assert m.unanswerable() == {"answered without the check": 1.0, "answered with the check": 0.0}
    assert (pct(m.check_cost()), round(m.check_cost() * 540)) == (11.9, 64)
    a = m.agent_run()
    assert (pct(a["unguarded"]["future"]), pct(a["unguarded"]["right"])) == (80.8, 19.2)
    assert a["guarded"] == {"future": 0.0, "right": 1.0, "logged calls": 400}


def test_exercises():
    idf = math.log(1 + (540 - 45 + 0.5) / (45 + 0.5))
    assert (round(1 + 495.5 / 45.5, 2), round(idf, 2), 1 * 2.5 / (1 + 1.5)) == (11.89, 2.48, 1.0)
    n_contam = len([d for d in m.headlines() if d["date"] < 1210])
    assert (n_contam, 5972 + 2016) == (7988, 7988) and round(n_contam / 5972 - 1, 2) == 0.34
