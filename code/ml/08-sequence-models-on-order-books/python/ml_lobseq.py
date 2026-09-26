"""Sequence models on order books (One Quant Book 12, chapter 8).

Ten-minute firm.tape sessions on disjoint seeds: eight for training, three for early stopping, eight for testing, and
eight more to double the training set. Ten-level book snapshots every half second; windows of the last 20 snapshots (ten
seconds); the label is the direction of the mean mid over the next ten seconds against the current mid (down, flat, up,
with a quarter-tick dead band). A multinomial logistic regression on hand-built order-flow and imbalance features is the
baseline; a CNN, an LSTM, a temporal convolutional network and a one-layer transformer are the sequence models, two
seeds each, scored per test session; and the TCN's score as the training set grows from four to sixteen sessions.
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("lobseq", "tape", "intraml"):
    sys.path.insert(0, str(ROOT / c))
from firm_intraml import features  # noqa: E402
from firm_lobseq import CNN, TCN, Attention, LSTMNet, Scaler, evaluate, snapshots, train, windows  # noqa: E402
from firm_tape import TapeConfig, simulate  # noqa: E402

T, H, STEP, SECONDS = 20, 20, 0.5, 600
TRAIN, VAL, TEST, EXTRA = range(300, 308), range(308, 311), range(311, 319), range(330, 338)
MODELS = {"CNN": CNN, "LSTM": LSTMNet, "TCN": TCN, "attention": Attention}


@functools.lru_cache(maxsize=32)
def session(seed):
    tape = simulate(TapeConfig(seconds=SECONDS, news_at=None, seed=seed))
    times, S, mid = snapshots(tape, step=STEP)
    X, y, fwd, idx = windows(S, mid, T, H)
    _, F, _, _ = features(tape, step=STEP)                              # same clock: from 30 s every half second
    return X, y, fwd, F[idx]


def _stack(seeds):
    parts = [session(s) for s in seeds]
    return tuple(np.concatenate([p[k] for p in parts]) for k in range(4))


@functools.lru_cache(maxsize=1)
def datasets():
    X, y, f, F = _stack(TRAIN)
    sc = Scaler().fit(X)
    Xv, yv, fv, Fv = _stack(VAL)
    tests = [session(s) for s in TEST]
    return {"train": (sc.transform(X), y, f, F), "val": (sc.transform(Xv), yv, fv, Fv),
            "test": [(sc.transform(a), b, c, d) for a, b, c, d in tests]}


def class_shares():
    y = datasets()["train"][1]
    return np.bincount(y, minlength=3) / len(y)


@functools.lru_cache(maxsize=1)
def logistic():
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    d = datasets()
    _, y, _, F = d["train"]
    sc = StandardScaler().fit(F)
    m = LogisticRegression(max_iter=2000, C=1.0).fit(sc.transform(F), y)
    out = []
    for _, yt, ft, Ft in d["test"]:
        p = m.predict_proba(sc.transform(Ft))
        out.append((float(np.mean(p.argmax(axis=1) == yt)), float(np.corrcoef(p[:, 2] - p[:, 0], ft)[0, 1])))
    return np.array(out)


@functools.lru_cache(maxsize=16)
def sequence(name, seed=1):
    import torch

    torch.manual_seed(seed)
    d = datasets()
    X, y, _, _ = d["train"]
    Xv, yv, _, _ = d["val"]
    dim = X.shape[2]
    model = MODELS[name](dim, T) if name == "attention" else MODELS[name](dim)
    model, hist, best = train(model, X, y, Xv, yv, seed=seed)
    res = [evaluate(model, a, b, c) for a, b, c, _ in d["test"]]
    return np.array([(r["accuracy"], r["ic"]) for r in res]), best


def table(seeds=(1, 2)):
    rows = {"logistic (OFI, imbalance)": logistic()}
    for name in MODELS:
        rows[name] = np.stack([sequence(name, s)[0] for s in seeds])   # (seeds, sessions, 2)
    return rows


@functools.lru_cache(maxsize=4)
def scaling(n_sessions, seed=1, name="TCN"):
    """Mean test IC of the TCN (and of the logistic baseline) trained on the first 4, the 8, or the 8 + 8 sessions."""
    import torch
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    seeds = (list(TRAIN) + list(EXTRA))[:n_sessions]
    X, y, _, F = _stack(seeds)
    sc = Scaler().fit(X)
    Xv, yv, _, _ = _stack(VAL)
    tests = [session(s) for s in TEST]
    torch.manual_seed(seed)
    model, _, _ = train(MODELS[name](X.shape[2]), sc.transform(X), y, sc.transform(Xv), yv, seed=seed)
    ic = np.mean([evaluate(model, sc.transform(a), b, c)["ic"] for a, b, c, _ in tests])
    s2 = StandardScaler().fit(F)
    lg = LogisticRegression(max_iter=2000).fit(s2.transform(F), y)
    li = np.mean([np.corrcoef(lg.predict_proba(s2.transform(Ft))[:, 2] - lg.predict_proba(s2.transform(Ft))[:, 0],
                              ft)[0, 1] for _, _, ft, Ft in tests])
    return float(ic), float(li)
