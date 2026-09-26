"""firm.nettab -- small neural networks for noisy tabular data (build of One Quant Book 12, chapter 7).

A deterministic PyTorch training loop for multilayer perceptrons on CPU: one thread, deterministic algorithms, every
random draw (initialisation, dropout, batch order) from one seed; early stopping on a purged validation block; seed
ensembles; and a content hash of the fitted weights, so that a model can be identified and reproduced bit for bit.

API (stable):
    set_determinism(threads=1)
    MLP(p, hidden=(32, 16), dropout=0.0, norm=None | 'batch' | 'layer', activation='relu')   a torch.nn.Module
    fit(X, y, Xv, yv, hidden, dropout, norm, lr, weight_decay, batch, epochs, patience, seed) -> Fitted
    Fitted.predict(X) -> ndarray; Fitted.history (validation losses per epoch); Fitted.best_epoch; Fitted.state_hash()
    SeedEnsemble(seeds, **fit_kwargs).fit(X, y, Xv, yv).predict(X)
Inputs are standardised with the training mean and standard deviation inside fit (stored with the model); the target is
scaled by its training standard deviation and the predictions scaled back.
"""
from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass, field

import numpy as np
import torch
from torch import nn


def set_determinism(threads: int = 1):
    torch.set_num_threads(threads)
    torch.use_deterministic_algorithms(True)


class MLP(nn.Module):
    def __init__(self, p: int, hidden=(32, 16), dropout: float = 0.0, norm=None, activation: str = "relu"):
        super().__init__()
        act = {"relu": nn.ReLU, "tanh": nn.Tanh, "gelu": nn.GELU}[activation]
        layers, d = [], p
        for h in hidden:
            layers.append(nn.Linear(d, h))
            if norm == "batch":
                layers.append(nn.BatchNorm1d(h))
            elif norm == "layer":
                layers.append(nn.LayerNorm(h))
            layers.append(act())
            if dropout > 0:
                layers.append(nn.Dropout(dropout))
            d = h
        layers.append(nn.Linear(d, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x).squeeze(-1)


@dataclass
class Fitted:
    model: MLP
    mu: np.ndarray
    sd: np.ndarray
    ysd: float
    history: list = field(default_factory=list)
    best_epoch: int = 0

    def predict(self, X) -> np.ndarray:
        self.model.eval()
        with torch.no_grad():
            z = torch.as_tensor((np.asarray(X, np.float32) - self.mu) / self.sd)
            return self.model(z).numpy().astype(float) * self.ysd

    def state_hash(self) -> str:
        h = hashlib.sha256()
        for k, v in self.model.state_dict().items():
            h.update(k.encode())
            h.update(v.detach().cpu().numpy().tobytes())
        return h.hexdigest()[:16]


def fit(X, y, Xv, yv, hidden=(32, 16), dropout: float = 0.0, norm=None, lr: float = 1e-3, weight_decay: float = 0.0,
        batch: int = 512, epochs: int = 30, patience: int = 5, seed: int = 1, activation: str = "relu") -> Fitted:
    set_determinism()
    g = torch.Generator().manual_seed(seed)
    torch.manual_seed(seed)
    X = np.asarray(X, np.float32)
    mu, sd = X.mean(axis=0), X.std(axis=0) + 1e-8
    ysd = float(np.std(y)) or 1.0
    Xt = torch.as_tensor((X - mu) / sd)
    yt = torch.as_tensor(np.asarray(y, np.float32) / ysd)
    Xvt = torch.as_tensor((np.asarray(Xv, np.float32) - mu) / sd)
    yvt = torch.as_tensor(np.asarray(yv, np.float32) / ysd)
    model = MLP(X.shape[1], hidden, dropout, norm, activation)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    best, best_state, best_ep, bad, hist = np.inf, None, 0, 0, []
    n = len(Xt)
    for ep in range(epochs):
        model.train()
        perm = torch.randperm(n, generator=g)
        for i in range(0, n, batch):
            idx = perm[i:i + batch]
            if len(idx) < 2:
                continue
            opt.zero_grad()
            loss = ((model(Xt[idx]) - yt[idx]) ** 2).mean()
            loss.backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            v = float(((model(Xvt) - yvt) ** 2).mean())
        hist.append(v)
        if v < best - 1e-7:
            best, best_state, best_ep, bad = v, copy.deepcopy(model.state_dict()), ep + 1, 0
        else:
            bad += 1
            if bad >= patience:
                break
    model.load_state_dict(best_state)
    return Fitted(model, mu, sd, ysd, hist, best_ep)


class SeedEnsemble:
    def __init__(self, seeds=(1, 2, 3, 4, 5), **kw):
        self.seeds, self.kw = seeds, kw

    def fit(self, X, y, Xv, yv):
        self.members = [fit(X, y, Xv, yv, seed=s, **self.kw) for s in self.seeds]
        return self

    def predict(self, X):
        return np.mean([m.predict(X) for m in self.members], axis=0)
