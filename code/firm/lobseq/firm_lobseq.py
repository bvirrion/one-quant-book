"""firm.lobseq -- sequence models on order-book streams (build of One Quant Book 12, chapter 8).

Order-book snapshots sampled on a clock from message-level sessions (firm.tape now, Book 10's exchange simulator when
its recorded tape is available through the same Tape arrays), windows of the last T snapshots as inputs, and the
direction of the mid price a few seconds ahead as the label (down, flat, up), as in the DeepLOB literature. Four small
sequence models in PyTorch -- a one-dimensional convolutional network, an LSTM, a temporal convolutional network and a
one-layer transformer encoder -- and a training loop that is deterministic on one CPU thread. Sessions never mix:
windows stay inside a session, and normalisation is fitted on training sessions only.

API (stable):
    snapshots(tape, step, levels, start) -> (times, S (n, 4 levels), mid ticks)   per level: distance of the bid and of
                                          the ask from the mid (ticks) and log1p of their sizes in lots
    windows(S, mid, T, horizon, threshold) -> (X (m, T, d), y (m,) in {0 down, 1 flat, 2 up}, fwd (m,), idx (m,))
                                          label: mean mid over the next `horizon` snapshots minus the current mid
    Scaler: fit on training windows' feature columns; transform(X)
    CNN(d), LSTMNet(d), TCN(d), Attention(d, T)       small classifiers returning logits (m, 3)
    train(model, X, y, Xv, yv, epochs, lr, batch, patience, seed) -> (model, history, best_epoch)
    evaluate(model, X, y, fwd) -> dict(accuracy, ic)  ic: correlation of p(up) - p(down) with the forward change
"""
from __future__ import annotations

import copy

import numpy as np
import torch
from torch import nn


def snapshots(tape, step: float = 0.5, levels: int = 10, start: float = 30.0):
    import pathlib
    import sys

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tape"))
    from firm_tape import Book

    msgs = tape.msgs
    times = np.arange(start, tape.cfg.seconds - 1e-9, step)
    lot = tape.cfg.lot
    book = Book()
    S = np.zeros((len(times), 4 * levels), np.float32)
    mids = np.zeros(len(times))
    j = 0
    for i, t in enumerate(times):
        while j < len(msgs) and msgs[j]["t"] <= t:
            book.apply(msgs[j])
            j += 1
        bids, asks = book.depth(1, levels), book.depth(-1, levels)
        mid = 0.5 * (bids[0][0] + asks[0][0])
        mids[i] = mid
        for k in range(levels):
            bp, bq = bids[k] if k < len(bids) else (bids[-1][0] - (k - len(bids) + 1), 0)
            ap, aq = asks[k] if k < len(asks) else (asks[-1][0] + (k - len(asks) + 1), 0)
            S[i, 4 * k:4 * k + 4] = (mid - bp, np.log1p(bq / lot), ap - mid, np.log1p(aq / lot))
    return times, S, mids


def windows(S, mid, T: int = 40, horizon: int = 10, threshold: float = 0.25):
    n = len(S)
    idx = np.arange(T - 1, n - horizon)
    fut = np.array([mid[i + 1:i + 1 + horizon].mean() for i in idx]) - mid[idx]
    y = np.where(fut > threshold, 2, np.where(fut < -threshold, 0, 1))
    X = np.stack([S[i - T + 1:i + 1] for i in idx])
    return X, y, fut, idx


class Scaler:
    def fit(self, X):
        flat = X.reshape(-1, X.shape[-1])
        self.mu, self.sd = flat.mean(axis=0), flat.std(axis=0) + 1e-6
        return self

    def transform(self, X):
        return ((X - self.mu) / self.sd).astype(np.float32)


class CNN(nn.Module):
    def __init__(self, d, h=32):
        super().__init__()
        self.net = nn.Sequential(nn.Conv1d(d, h, 5, padding=2), nn.ReLU(), nn.Conv1d(h, h, 5, padding=2), nn.ReLU(),
                                 nn.AdaptiveAvgPool1d(1), nn.Flatten(), nn.Linear(h, 3))

    def forward(self, x):                                              # x: (m, T, d)
        return self.net(x.transpose(1, 2))


class LSTMNet(nn.Module):
    def __init__(self, d, h=32):
        super().__init__()
        self.lstm = nn.LSTM(d, h, batch_first=True)
        self.out = nn.Linear(h, 3)

    def forward(self, x):
        o, _ = self.lstm(x)
        return self.out(o[:, -1])


class _CausalConv(nn.Module):
    def __init__(self, cin, cout, k, dil):
        super().__init__()
        self.pad = (k - 1) * dil
        self.conv = nn.Conv1d(cin, cout, k, dilation=dil)

    def forward(self, x):
        return self.conv(nn.functional.pad(x, (self.pad, 0)))


class TCN(nn.Module):
    """Dilated causal convolutions (dilations 1, 2, 4, 8) with residual connections; the last step feeds the head."""

    def __init__(self, d, h=32, k=3):
        super().__init__()
        self.inp = nn.Conv1d(d, h, 1)
        self.blocks = nn.ModuleList([_CausalConv(h, h, k, 2**i) for i in range(4)])
        self.out = nn.Linear(h, 3)

    def forward(self, x):
        z = self.inp(x.transpose(1, 2))
        for b in self.blocks:
            z = z + torch.relu(b(z))
        return self.out(z[:, :, -1])


class Attention(nn.Module):
    """One transformer-encoder layer (two heads) over the window, with learned positions; the last step feeds the
    head."""

    def __init__(self, d, T, h=32):
        super().__init__()
        self.inp = nn.Linear(d, h)
        self.pos = nn.Parameter(torch.zeros(1, T, h))
        self.enc = nn.TransformerEncoderLayer(h, nhead=2, dim_feedforward=64, dropout=0.0, batch_first=True)
        self.out = nn.Linear(h, 3)

    def forward(self, x):
        z = self.enc(self.inp(x) + self.pos)
        return self.out(z[:, -1])


def train(model, X, y, Xv, yv, epochs: int = 15, lr: float = 1e-3, batch: int = 256, patience: int = 4,
          seed: int = 1):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    g = torch.Generator().manual_seed(seed)
    Xt, yt = torch.as_tensor(X), torch.as_tensor(y, dtype=torch.long)
    Xvt, yvt = torch.as_tensor(Xv), torch.as_tensor(yv, dtype=torch.long)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    lossf = nn.CrossEntropyLoss()
    best, best_state, best_ep, bad, hist = np.inf, None, 0, 0, []
    for ep in range(epochs):
        model.train()
        perm = torch.randperm(len(Xt), generator=g)
        for i in range(0, len(Xt), batch):
            b = perm[i:i + batch]
            opt.zero_grad()
            lossf(model(Xt[b]), yt[b]).backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            v = float(lossf(model(Xvt), yvt))
        hist.append(v)
        if v < best - 1e-6:
            best, best_state, best_ep, bad = v, copy.deepcopy(model.state_dict()), ep + 1, 0
        else:
            bad += 1
            if bad >= patience:
                break
    model.load_state_dict(best_state)
    return model, hist, best_ep


def evaluate(model, X, y, fwd) -> dict:
    model.eval()
    with torch.no_grad():
        p = torch.softmax(model(torch.as_tensor(X)), dim=1).numpy()
    score = p[:, 2] - p[:, 0]
    return {"accuracy": float(np.mean(p.argmax(axis=1) == y)), "ic": float(np.corrcoef(score, fwd)[0, 1])}
