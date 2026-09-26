"""Representation learning (One Quant Book 12, chapter 10).

A desk with many sessions of order-book data and labels for few of them. Sixteen unlabelled ten-minute firm.tape
sessions pre-train two encoders of five-second order-book windows (ten half-second snapshots of ten levels, 400
numbers): a denoising autoencoder and a contrastive encoder. With one, two or four labelled sessions, a ridge probe on
the frozen codes, the pre-trained encoder fine-tuned, the same network trained from scratch, and ridge on the raw
window are scored on six test sessions by the information coefficient of their forecast of the next ten seconds' mean
mid change; ridge on the hand-made order-flow features of chapter 8 is the reference.
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("represent", "lobseq", "tape", "intraml"):
    sys.path.insert(0, str(ROOT / c))
from firm_intraml import features  # noqa: E402
from firm_lobseq import snapshots, windows  # noqa: E402
from firm_represent import (  # noqa: E402
    encode,
    fine_tune,
    linear_probe,
    pretrain_contrastive,
    pretrain_dae,
    pretrain_predictive,
    scratch,
)
from firm_tape import TapeConfig, simulate  # noqa: E402

T, H, AHEAD = 10, 20, 4
UNLAB, LAB, VAL, TEST = range(500, 516), range(600, 604), range(604, 605), range(610, 616)


@functools.lru_cache(maxsize=64)
def session(seed, ahead=AHEAD):
    tape = simulate(TapeConfig(seconds=600, news_at=None, seed=seed))
    _, S, mid = snapshots(tape, step=0.5)
    X, _, fwd, idx = windows(S, mid, T, H)
    _, F, _, _ = features(tape, step=0.5)
    fut = np.minimum(idx + ahead, len(S) - 1)
    return X.reshape(len(X), -1), fwd, F[idx], S[fut] - S[idx]


def _stack(seeds, ahead=AHEAD):
    parts = [session(s, ahead) for s in seeds]
    return tuple(np.concatenate([p[k] for p in parts]) for k in range(4))


@functools.lru_cache(maxsize=1)
def scaler():
    X = _stack(UNLAB)[0]
    return X.mean(axis=0), X.std(axis=0) + 1e-6


def _z(X):
    mu, sd = scaler()
    return ((X - mu) / sd).astype(np.float32)


@functools.lru_cache(maxsize=2)
def encoders(seed=1, ahead=AHEAD):
    X, _, _, A = _stack(UNLAB, ahead)
    A = (A - A.mean(axis=0)) / (A.std(axis=0) + 1e-6)
    return {"autoencoder": pretrain_dae(_z(X), seed=seed), "contrastive": pretrain_contrastive(_z(X), seed=seed),
            "predictive": pretrain_predictive(_z(X), A.astype(np.float32), seed=seed)}


def _ic(pred_by_session):
    tests = [session(s) for s in TEST]
    return float(np.mean([np.corrcoef(p, t[1])[0, 1] for p, t in zip(pred_by_session, tests, strict=True)]))


def _one(X, y, F, Xv, yv, enc, seed):
    tests = [session(s) for s in TEST]
    out = {"raw ridge": _ic([linear_probe(_z(X), y, _z(t[0]), alpha=1e3) for t in tests]),
           "features ridge": _ic([linear_probe(F, y, t[2]) for t in tests])}
    for name, e in enc.items():
        out[name + " probe"] = _ic([linear_probe(encode(e, _z(X)), y, encode(e, _z(t[0]))) for t in tests])
    ft = fine_tune(enc["predictive"], _z(X), y, _z(Xv), yv, seed=seed)
    sc = scratch(_z(X), y, _z(Xv), yv, seed=seed)
    out["predictive fine-tuned"] = _ic([ft(_z(t[0])) for t in tests])
    out["from scratch"] = _ic([sc(_z(t[0])) for t in tests])
    return out


@functools.lru_cache(maxsize=8)
def compare(n_windows, seed=1, ahead=AHEAD):
    """With n_windows labelled windows: the average test IC over four draws (the first n_windows windows of each
    labelled session); n_windows = 0 means all four sessions together (one draw)."""
    Xv, yv, _, _ = _stack(VAL)
    enc = encoders(seed, ahead)
    if n_windows == 0:
        X, y, F, _ = _stack(LAB)
        return _one(X, y, F, Xv, yv, enc, seed)
    runs = []
    for s in LAB:
        X, y, F, _ = (a[:n_windows] for a in session(s))
        runs.append(_one(X, y, F, Xv, yv, enc, seed))
    return {k: float(np.mean([r[k] for r in runs])) for k in runs[0]}
