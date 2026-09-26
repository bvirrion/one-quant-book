"""firm.represent -- representation learning on unlabelled market data (build of One Quant Book 12, chapter 10).

Encoders pre-trained without labels on market windows (flattened order-book snapshots or any (m, d) array of inputs),
by two self-supervised objectives: reconstruction of a masked, noisy input (a denoising autoencoder) and a contrastive
objective that pulls two augmented views of the same window together and pushes other windows apart (InfoNCE, as in
SimCLR). The learned codes then feed a linear probe (ridge regression) or are fine-tuned with a small head on the few
labelled windows available. One CPU thread, deterministic algorithms, every draw from the run's seed.

API (stable):
    Encoder(d_in, code, hidden)                        an MLP encoder
    augment(x, gen, noise, mask)                       Gaussian jitter and random feature masking (a view)
    pretrain_dae(X, code, hidden, mask, noise, epochs, seed) -> Encoder
    pretrain_contrastive(X, code, hidden, noise, mask, tau, epochs, seed) -> Encoder
    pretrain_predictive(X, Y, code, hidden, epochs, seed) -> Encoder   self-supervised forecasting of label-free Y
    info_nce(z1, z2, tau)                              the contrastive loss of a batch of paired views
    encode(enc, X) -> (m, code) ndarray
    linear_probe(Z, y, Zt, alpha) -> predictions      ridge on frozen codes
    fine_tune(enc, X, y, Xv, yv, lr, epochs, patience, seed) -> callable predicting y
    scratch(X, y, Xv, yv, code, hidden, epochs, patience, seed) -> callable   the same network trained from random init
"""
from __future__ import annotations

import copy

import numpy as np
import torch
from torch import nn


def _det(seed):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed)
    return torch.Generator().manual_seed(seed)


class Encoder(nn.Module):
    def __init__(self, d_in, code=16, hidden=(64,)):
        super().__init__()
        layers, d = [], d_in
        for h in hidden:
            layers += [nn.Linear(d, h), nn.ReLU()]
            d = h
        self.net = nn.Sequential(*layers, nn.Linear(d, code))

    def forward(self, x):
        return self.net(x)


def augment(x, gen, noise: float = 0.3, mask: float = 0.2):
    keep = (torch.rand(x.shape, generator=gen) > mask).float()
    return x * keep + noise * torch.randn(x.shape, generator=gen)


def pretrain_dae(X, code=16, hidden=(64,), mask=0.2, noise=0.3, epochs=10, seed=1, batch=256, lr=1e-3):
    g = _det(seed)
    enc = Encoder(X.shape[1], code, hidden)
    dec = nn.Sequential(nn.Linear(code, hidden[-1]), nn.ReLU(), nn.Linear(hidden[-1], X.shape[1]))
    opt = torch.optim.Adam(list(enc.parameters()) + list(dec.parameters()), lr=lr)
    Xt = torch.as_tensor(X, dtype=torch.float32)
    for _ in range(epochs):
        perm = torch.randperm(len(Xt), generator=g)
        for i in range(0, len(Xt), batch):
            b = Xt[perm[i:i + batch]]
            opt.zero_grad()
            ((dec(enc(augment(b, g, noise, mask))) - b) ** 2).mean().backward()
            opt.step()
    return enc


def info_nce(z1, z2, tau: float = 0.2):
    """Symmetric InfoNCE: each view must pick its partner among the batch's 2m - 1 other views."""
    z = nn.functional.normalize(torch.cat([z1, z2]), dim=1)
    s = z @ z.T / tau
    s.fill_diagonal_(-1e9)
    m = len(z1)
    target = torch.cat([torch.arange(m, 2 * m), torch.arange(0, m)])
    return nn.functional.cross_entropy(s, target)


def pretrain_contrastive(X, code=16, hidden=(64,), noise=0.3, mask=0.2, tau=0.2, epochs=10, seed=1, batch=256,
                         lr=1e-3):
    g = _det(seed)
    enc = Encoder(X.shape[1], code, hidden)
    proj = nn.Sequential(nn.ReLU(), nn.Linear(code, code))
    opt = torch.optim.Adam(list(enc.parameters()) + list(proj.parameters()), lr=lr)
    Xt = torch.as_tensor(X, dtype=torch.float32)
    for _ in range(epochs):
        perm = torch.randperm(len(Xt), generator=g)
        for i in range(0, len(Xt) - 1, batch):
            b = Xt[perm[i:i + batch]]
            if len(b) < 2:
                continue
            opt.zero_grad()
            info_nce(proj(enc(augment(b, g, noise, mask))), proj(enc(augment(b, g, noise, mask))), tau).backward()
            opt.step()
    return enc


def pretrain_predictive(X, Y, code=16, hidden=(64,), epochs=10, seed=1, batch=256, lr=1e-3):
    """Self-supervised forecasting: the encoder, with a linear head, predicts Y -- any label-free future of the input
    (here the change of the book snapshot a few seconds later), the way a language model predicts the next word."""
    g = _det(seed)
    enc = Encoder(X.shape[1], code, hidden)
    head = nn.Linear(code, Y.shape[1])
    opt = torch.optim.Adam(list(enc.parameters()) + list(head.parameters()), lr=lr)
    Xt, Yt = torch.as_tensor(X, dtype=torch.float32), torch.as_tensor(Y, dtype=torch.float32)
    for _ in range(epochs):
        perm = torch.randperm(len(Xt), generator=g)
        for i in range(0, len(Xt), batch):
            b = perm[i:i + batch]
            opt.zero_grad()
            ((head(enc(Xt[b])) - Yt[b]) ** 2).mean().backward()
            opt.step()
    return enc


def encode(enc, X):
    enc.eval()
    with torch.no_grad():
        return enc(torch.as_tensor(X, dtype=torch.float32)).numpy().astype(float)


def linear_probe(Z, y, Zt, alpha: float = 1.0):
    from sklearn.linear_model import Ridge

    mu, sd = Z.mean(axis=0), Z.std(axis=0) + 1e-9
    return Ridge(alpha=alpha).fit((Z - mu) / sd, y).predict((Zt - mu) / sd)


def _fit_head(enc, X, y, Xv, yv, lr, epochs, patience, seed, train_encoder=True, batch=128):
    g = _det(seed)
    head = nn.Linear(enc.net[-1].out_features, 1)
    params = list(head.parameters()) + (list(enc.parameters()) if train_encoder else [])
    opt = torch.optim.Adam(params, lr=lr)
    ys = float(np.std(y)) or 1.0
    Xt, yt = torch.as_tensor(X, dtype=torch.float32), torch.as_tensor(y / ys, dtype=torch.float32)
    Xvt, yvt = torch.as_tensor(Xv, dtype=torch.float32), torch.as_tensor(yv / ys, dtype=torch.float32)
    model = nn.Sequential(enc, head)
    best, state, bad = np.inf, None, 0
    for _ in range(epochs):
        model.train()
        perm = torch.randperm(len(Xt), generator=g)
        for i in range(0, len(Xt), batch):
            b = perm[i:i + batch]
            opt.zero_grad()
            ((model(Xt[b]).squeeze(-1) - yt[b]) ** 2).mean().backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            v = float(((model(Xvt).squeeze(-1) - yvt) ** 2).mean())
        if v < best - 1e-7:
            best, state, bad = v, copy.deepcopy(model.state_dict()), 0
        else:
            bad += 1
            if bad >= patience:
                break
    model.load_state_dict(state)
    model.eval()

    def predict(Xn):
        with torch.no_grad():
            return model(torch.as_tensor(Xn, dtype=torch.float32)).squeeze(-1).numpy().astype(float) * ys

    return predict


def fine_tune(enc, X, y, Xv, yv, lr=3e-4, epochs=30, patience=4, seed=1):
    return _fit_head(copy.deepcopy(enc), X, y, Xv, yv, lr, epochs, patience, seed)


def scratch(X, y, Xv, yv, code=16, hidden=(64,), lr=1e-3, epochs=30, patience=4, seed=1):
    _det(seed)
    return _fit_head(Encoder(X.shape[1], code, hidden), X, y, Xv, yv, lr, epochs, patience, seed)
