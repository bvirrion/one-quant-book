import math
import pathlib
import sys

import numpy as np
import torch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
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

CORPUS = [["a", "b", "c", "x"], ["a", "b", "d", "y"], ["e", "b", "c", "z"], ["e", "f", "c", "x"]]


def _fit(seed=0, epochs=60):
    V = Vocab(CORPUS)
    m = TinyLM(len(V), d=16, heads=2, layers=1, max_len=8)
    losses = train_lm(m, [V.encode(s) for s in CORPUS], epochs=epochs, lr=1e-2, batch=4, seed=seed)
    return V, m, losses


def test_memorises_a_small_corpus_and_is_deterministic():
    V, m, losses = _fit()
    assert losses[-1] < losses[0] / 3
    lp = next_logprobs(m, [V.encode(s[:3]) for s in CORPUS])
    assert [V.itos[i] for i in lp.argmax(1)] == [s[3] for s in CORPUS]
    _, m2, losses2 = _fit()
    assert losses == losses2
    assert all(torch.equal(a, b) for a, b in zip(m.state_dict().values(), m2.state_dict().values(), strict=True))


def test_causal():
    V, m, _ = _fit(epochs=5)
    a = torch.as_tensor([V.encode(["a", "b", "c", "x"])])
    b = torch.as_tensor([V.encode(["a", "b", "c", "y"])])
    with torch.no_grad():
        la, lb = m(a), m(b)
    assert torch.allclose(la[:, :3], lb[:, :3], atol=1e-6) and not torch.allclose(la[:, 3], lb[:, 3])


def test_bm25_formula():
    docs = [["apple", "pie"], ["apple", "apple", "tart", "cake"], ["cake"]]
    s = BM25(docs, k1=1.5, b=0.75).scores(["apple"])
    idf = math.log(1 + (3 - 2 + 0.5) / (2 + 0.5))
    avg = 7 / 3
    want = [idf * f * 2.5 / (f + 1.5 * (1 - 0.75 + 0.75 * n / avg)) for f, n in ((1, 2), (2, 4))] + [0.0]
    assert np.allclose(s, want)
    assert BM25(docs).scores(["unknown"]).tolist() == [0.0, 0.0, 0.0]


def test_dense_expansion_and_hybrid():
    vocab = ["sales", "revenue", "debt"]
    V = np.array([[1.0, 0.0], [0.999, 0.0447], [0.0, 1.0]])
    V /= np.linalg.norm(V, axis=1, keepdims=True)
    assert expand_query(["sales", "of", "x"], vocab, V) == ["sales", "of", "x", "revenue"]
    assert np.allclose(dense_scores(np.array([[2.0, 0.0], [0.0, 3.0]]), np.array([1.0, 0.0])), [1.0, 0.0])
    h = hybrid([1.0, 2.0, 3.0], [3.0, 2.0, 1.0], w=1.0)
    assert np.allclose(h, 0.0)


def test_registry_guard_and_log():
    docs = [{"id": 1, "published": 5}, {"id": 2, "published": 15}]

    def search(as_of=None):
        return [d for d in docs if as_of is None or d["published"] <= as_of]

    def leaky(as_of=None):
        return docs

    reg = ToolRegistry(as_of=10)
    reg.register("search", search, dated=True)
    reg.register("leaky", leaky, dated=True)
    assert reg.call("search") == [docs[0]]
    assert reg.call("search", as_of=20) is None
    assert reg.call("leaky") is None
    assert reg.call("nothing") is None
    assert [e["status"] for e in reg.log] == ["ok", "refused: after the as-of date", "refused: result after the as-of date",
                                              "unknown tool"]
