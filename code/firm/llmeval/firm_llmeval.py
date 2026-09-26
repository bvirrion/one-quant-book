"""firm.llmeval -- language models evaluated without leakage, retrieval, and a point-in-time agent harness (Book 12,
chapter 14).

Nothing here downloads weights or calls a network service. A tiny word-level transformer, trained in seconds, stands in
for a large language model so that the evaluation protocol can be tested on a model whose training data are known
exactly: a cut-off split, the memorisation premium (accuracy on documents before the model's training cut-off minus
after), and the anonymisation test (the accuracy lost when names and dates are replaced by placeholders). Retrieval is
BM25 and dense (embedding) search, and their hybrid; the agent harness runs tools from a registry behind a
point-in-time guard that refuses any document published after the as-of date, and logs every call.

API (stable):
    Vocab(tokens_lists, specials) .encode(tokens) .decode(ids) .id(token)
    TinyLM(vocab_size, d, heads, layers, max_len)       causal transformer language model
    train_lm(model, seqs, epochs, lr, batch, seed) -> losses per epoch     next-token cross-entropy, deterministic
    next_logprobs(model, prefixes) -> (m, vocab) log-probabilities of the next token after each prefix
    BM25(docs, k1, b) .scores(query) -> array                              Robertson-Zaragoza BM25
    dense_scores(doc_vecs, query_vec) -> cosine similarities
    expand_query(tokens, vocab, vectors, threshold) -> tokens plus their embedding neighbours
    hybrid(a, b, w) -> standardised a + w * standardised b
    ToolRegistry(as_of) .register(name, fn, dated) .call(name, **kw) ; .log   point-in-time tool calls
"""
from __future__ import annotations

import math
from collections import Counter

import numpy as np
import torch
from torch import nn


class Vocab:
    def __init__(self, token_lists, specials=("<pad>", "<unk>")):
        cnt = Counter(t for toks in token_lists for t in toks)
        self.itos = list(specials) + sorted(t for t in cnt if t not in specials)
        self.stoi = {t: i for i, t in enumerate(self.itos)}

    def __len__(self):
        return len(self.itos)

    def id(self, t):
        return self.stoi.get(t, self.stoi["<unk>"])

    def encode(self, tokens):
        return [self.id(t) for t in tokens]

    def decode(self, ids):
        return [self.itos[i] for i in ids]


class TinyLM(nn.Module):
    """Token and position embeddings, a stack of causal self-attention layers, and a projection back onto the
    vocabulary: the architecture of a decoder-only language model at toy scale."""

    def __init__(self, vocab_size, d=64, heads=4, layers=2, max_len=32):
        super().__init__()
        self.tok = nn.Embedding(vocab_size, d)
        self.pos = nn.Embedding(max_len, d)
        layer = nn.TransformerEncoderLayer(d, heads, dim_feedforward=4 * d, dropout=0.0, batch_first=True)
        self.blocks = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
        self.out = nn.Linear(d, vocab_size)

    def forward(self, ids):                                              # ids: (m, T) -> logits (m, T, vocab)
        T = ids.shape[1]
        mask = torch.triu(torch.full((T, T), float("-inf")), diagonal=1)   # a token sees only its past
        z = self.tok(ids) + self.pos(torch.arange(T))[None]
        return self.out(self.blocks(z, mask=mask, is_causal=True))


def _pad(seqs, T=None):
    T = T or max(len(s) for s in seqs)
    out = torch.zeros((len(seqs), T), dtype=torch.long)
    for i, s in enumerate(seqs):
        out[i, :len(s)] = torch.as_tensor(s[:T])
    return out


def train_lm(model, seqs, epochs=20, lr=3e-3, batch=64, seed=0):
    """Next-token cross-entropy on every position (padding ignored); Adam; one thread, deterministic."""
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed)
    for mod in model.modules():                                         # initial weights from the seed alone
        for name in ("reset_parameters", "_reset_parameters"):          # (attention layers use the second name)
            if mod is not model and hasattr(mod, name):
                getattr(mod, name)()
    g = torch.Generator().manual_seed(seed)
    X = _pad(seqs)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    lossf = nn.CrossEntropyLoss(ignore_index=0)
    losses = []
    for _ in range(epochs):
        model.train()
        perm = torch.randperm(len(X), generator=g)
        tot, n = 0.0, 0
        for i in range(0, len(X), batch):
            xb = X[perm[i:i + batch]]
            opt.zero_grad()
            logits = model(xb[:, :-1])
            loss = lossf(logits.reshape(-1, logits.shape[-1]), xb[:, 1:].reshape(-1))
            loss.backward()
            opt.step()
            tot, n = tot + float(loss.detach()) * len(xb), n + len(xb)
        losses.append(tot / n)
    model.eval()
    return losses


def next_logprobs(model, prefixes, batch=512):
    """Log-probabilities of the token following each prefix (prefixes of any lengths)."""
    out = []
    with torch.no_grad():
        for i in range(0, len(prefixes), batch):
            ps = prefixes[i:i + batch]
            X = _pad(ps)
            logits = model(X)
            last = torch.as_tensor([len(p) - 1 for p in ps])
            out.append(torch.log_softmax(logits[torch.arange(len(ps)), last], -1).numpy())
    return np.concatenate(out)


class BM25:
    """score(q, d) = sum over query terms t of idf(t) * f(t,d) (k1 + 1) / (f(t,d) + k1 (1 - b + b |d| / avgdl)),
    idf(t) = log(1 + (N - n_t + 0.5) / (n_t + 0.5))."""

    def __init__(self, docs, k1=1.5, b=0.75):
        self.docs = [Counter(d) for d in docs]
        self.len = np.array([len(d) for d in docs], dtype=float)
        self.avg = self.len.mean()
        self.k1, self.b = k1, b
        df = Counter(t for d in docs for t in set(d))
        N = len(docs)
        self.idf = {t: math.log(1 + (N - n + 0.5) / (n + 0.5)) for t, n in df.items()}

    def scores(self, query):
        s = np.zeros(len(self.docs))
        norm = self.k1 * (1 - self.b + self.b * self.len / self.avg)
        for t in set(query):
            if t not in self.idf:
                continue
            f = np.array([d.get(t, 0) for d in self.docs], dtype=float)
            s += self.idf[t] * f * (self.k1 + 1) / (f + norm)
        return s


def dense_scores(doc_vecs, query_vec):
    d = doc_vecs / (np.linalg.norm(doc_vecs, axis=1, keepdims=True) + 1e-12)
    return d @ (query_vec / (np.linalg.norm(query_vec) + 1e-12))


def expand_query(tokens, vocab, vectors, threshold=0.9):
    """Add to a query every word whose embedding has cosine above `threshold` with one of its words (rows of `vectors`
    are unit length): lexical search that also finds the synonyms an embedding model has learned."""
    ix = {w: i for i, w in enumerate(vocab)}
    out = list(tokens)
    for t in tokens:
        if t in ix:
            sim = vectors @ vectors[ix[t]]
            out += [w for w, s in zip(vocab, sim, strict=True) if s > threshold and w != t and w not in out]
    return out


def hybrid(a, b, w=1.0):
    z = lambda x: (x - x.mean()) / (x.std() + 1e-12)                      # noqa: E731
    return z(np.asarray(a)) + w * z(np.asarray(b))


class ToolRegistry:
    """Tools called by name; a dated tool receives the registry's as-of date and must not return anything published
    after it. Every call, its arguments, its result size and any refusal go to the log."""

    def __init__(self, as_of):
        self.as_of, self.tools, self.log = as_of, {}, []

    def register(self, name, fn, dated=False):
        self.tools[name] = (fn, dated)

    def call(self, name, **kw):
        if name not in self.tools:
            self.log.append({"tool": name, "args": kw, "status": "unknown tool"})
            return None
        fn, dated = self.tools[name]
        if dated and kw.get("as_of", self.as_of) > self.as_of:
            self.log.append({"tool": name, "args": kw, "status": "refused: after the as-of date"})
            return None
        args = {"as_of": self.as_of} | kw if dated else kw
        out = fn(**args)
        if dated and any(r.get("published", -math.inf) > self.as_of for r in (out or [])):
            self.log.append({"tool": name, "args": kw, "status": "refused: result after the as-of date"})
            return None
        self.log.append({"tool": name, "args": kw, "status": "ok", "n": len(out) if hasattr(out, "__len__") else 1})
        return out
