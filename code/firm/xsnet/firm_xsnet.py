"""firm.xsnet -- cross-sectional deep models and learned factor models (build of One Quant Book 12, chapter 9).

Panels of assets: characteristics Z (T, n, L) known at the end of month t, returns r (T, n) of month t + 1. Three factor
models whose betas are, in turn, fixed per asset (PCA on the returns), linear in the characteristics (instrumented PCA,
Kelly, Pruitt and Su), and a neural network of the characteristics (the conditional autoencoder of Gu, Kelly and Xiu),
scored by total R-squared (betas times the month's realised factors) and predictive R-squared (betas times the average
training factor); and a pooled panel network with an entity embedding for a categorical identifier.

API (stable):
    managed(Z, r)                          (T, L) characteristic-managed portfolios Z_t' r_t / n (permutation invariant)
    PCAModel(K).fit(r).score(r, train_mean)                static loadings
    IPCA(K, iters).fit(Z, r) ; .factors(Z, r) ; .betas(Z) ; .score(Z, r)
    CondAE(L, K, hidden, seed).fit(Z, r, Zv, rv) ; .betas(Z) ; .factors(Z, r) ; .score(Z, r)
    scores(pred_total, pred_mu, r) -> (total R2, predictive R2)   both against zero
    EmbedMLP(n_cat, emb_dim, p, hidden, emb_init); fit_embed(cat, X, y, cat_v, X_v, y_v, emb_dim, seed, ...) -> model
                                           embeddings start at N(0, emb_init^2) (None: PyTorch's N(0, 1))
All neural fits: one CPU thread, deterministic algorithms, early stopping on validation months.
"""
from __future__ import annotations

import copy

import numpy as np
import torch
from torch import nn


def _r2(r, p):
    return float(1 - np.sum((r - p) ** 2) / np.sum(r**2))


def scores(pred_total, pred_mu, r):
    return _r2(r, pred_total), _r2(r, pred_mu)


def with_constant(Z):
    return np.concatenate([np.ones(Z.shape[:2] + (1,)), Z], axis=-1)


def managed(Z, r):
    return np.einsum("tnl,tn->tl", Z, r) / Z.shape[1]


class PCAModel:
    def __init__(self, K: int = 3):
        self.K = K

    def fit(self, r):
        _, _, vt = np.linalg.svd(r, full_matrices=False)
        self.B = vt[: self.K].T                                         # (n, K) static loadings
        self.lam = (r @ self.B @ np.linalg.inv(self.B.T @ self.B)).mean(axis=0)
        return self

    def score(self, r):
        f = r @ self.B @ np.linalg.inv(self.B.T @ self.B)
        return scores(f @ self.B.T, np.tile(self.B @ self.lam, (len(r), 1)), r)


class IPCA:
    """r_t = Z_t Gamma f_t + e_t (returns of month t + 1 on characteristics of month t), fitted by alternating least
    squares; Gamma is normalised to Gamma' Gamma = I and the factors are rotated to be orthogonal."""

    def __init__(self, K: int = 3, iters: int = 60):
        self.K, self.iters = K, iters

    def factors(self, Z, r):
        G = self.G
        return np.stack([np.linalg.solve(G.T @ z.T @ z @ G, G.T @ z.T @ x) for z, x in zip(Z, r, strict=True)])

    def fit(self, Z, r):
        X = managed(Z, r)
        _, _, vt = np.linalg.svd(X, full_matrices=False)
        self.G = vt[: self.K].T
        L, K = self.G.shape
        for _ in range(self.iters):
            F = self.factors(Z, r)
            A = np.zeros((L * K, L * K))
            b = np.zeros(L * K)
            for z, x, f in zip(Z, r, F, strict=True):
                A += np.kron(z.T @ z, np.outer(f, f))
                b += np.kron(z.T @ x, f)
            G = np.linalg.solve(A, b).reshape(L, K)
            q, _ = np.linalg.qr(G)                                      # Gamma' Gamma = I
            self.G = q
        F = self.factors(Z, r)
        w, V = np.linalg.eigh(F.T @ F)
        self.G = self.G @ V[:, ::-1]
        self.lam = self.factors(Z, r).mean(axis=0)
        return self

    def betas(self, Z):
        return Z @ self.G

    def score(self, Z, r):
        B = self.betas(Z)
        F = self.factors(Z, r)
        return scores(np.einsum("tnk,tk->tn", B, F), B @ self.lam, r)


class _CA(nn.Module):
    def __init__(self, L, K, hidden):
        super().__init__()
        layers, d = [], L
        for h in hidden:
            layers += [nn.Linear(d, h), nn.ReLU()]
            d = h
        self.beta = nn.Sequential(*layers, nn.Linear(d, K))
        self.fac = nn.Linear(L, K, bias=False)

    def forward(self, z, x):                                            # z: (m, n, L), x: (m, L)
        return torch.einsum("mnk,mk->mn", self.beta(z), self.fac(x))


class CondAE:
    """Conditional autoencoder: betas are a network of the characteristics, factors a linear map of the managed
    portfolios; trained to reproduce the month's returns (Gu, Kelly and Xiu, 2021)."""

    def __init__(self, L, K=3, hidden=(32, 16), seed=1, lr=1e-3, epochs=200, patience=15, weight_decay=1e-4):
        self.L, self.K, self.hidden, self.seed = L, K, hidden, seed
        self.lr, self.epochs, self.patience, self.wd = lr, epochs, patience, weight_decay

    def fit(self, Z, r, Zv, rv):
        torch.set_num_threads(1)
        torch.use_deterministic_algorithms(True)
        torch.manual_seed(self.seed)
        g = torch.Generator().manual_seed(self.seed)
        self.net = _CA(self.L, self.K, self.hidden)
        zt, rt = torch.as_tensor(Z, dtype=torch.float32), torch.as_tensor(r, dtype=torch.float32)
        xt = torch.as_tensor(managed(Z, r), dtype=torch.float32)
        zv, rv_t = torch.as_tensor(Zv, dtype=torch.float32), torch.as_tensor(rv, dtype=torch.float32)
        xv = torch.as_tensor(managed(Zv, rv), dtype=torch.float32)
        opt = torch.optim.AdamW(self.net.parameters(), lr=self.lr, weight_decay=self.wd)
        best, state, bad = np.inf, None, 0
        for _ in range(self.epochs):
            self.net.train()
            perm = torch.randperm(len(zt), generator=g)
            for i in range(0, len(zt), 8):                             # mini-batches of eight months
                b = perm[i:i + 8]
                opt.zero_grad()
                ((self.net(zt[b], xt[b]) - rt[b]) ** 2).mean().backward()
                opt.step()
            self.net.eval()
            with torch.no_grad():
                v = float(((self.net(zv, xv) - rv_t) ** 2).mean())
            if v < best - 1e-9:
                best, state, bad = v, copy.deepcopy(self.net.state_dict()), 0
            else:
                bad += 1
                if bad >= self.patience:
                    break
        self.net.load_state_dict(state)
        self.lam = self.factors(Z, r).mean(axis=0)
        return self

    def betas(self, Z):
        with torch.no_grad():
            return self.net.beta(torch.as_tensor(Z, dtype=torch.float32)).numpy().astype(float)

    def factors(self, Z, r):
        with torch.no_grad():
            return self.net.fac(torch.as_tensor(managed(Z, r), dtype=torch.float32)).numpy().astype(float)

    def score(self, Z, r):
        B = self.betas(Z)
        return scores(np.einsum("tnk,tk->tn", B, self.factors(Z, r)), B @ self.lam, r)


class EmbedMLP(nn.Module):
    """A pooled panel network whose input is the features and a learned embedding of a categorical identifier."""

    def __init__(self, n_cat, emb_dim, p, hidden=(32,), emb_init=0.01):
        super().__init__()
        self.emb = nn.Embedding(n_cat, emb_dim) if emb_dim > 0 else None
        if self.emb is not None and emb_init is not None:              # start near zero: learned values carry signal
            nn.init.normal_(self.emb.weight, std=emb_init)
        layers, d = [], p + max(emb_dim, 0)
        for h in hidden:
            layers += [nn.Linear(d, h), nn.ReLU()]
            d = h
        self.net = nn.Sequential(*layers, nn.Linear(d, 1))

    def forward(self, cat, x):
        z = x if self.emb is None else torch.cat([x, self.emb(cat)], dim=1)
        return self.net(z).squeeze(-1)


def fit_embed(cat, X, y, cat_v, X_v, y_v, emb_dim=2, seed=1, epochs=60, patience=6, lr=3e-3, emb_init=0.01):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed)
    g = torch.Generator().manual_seed(seed)
    m = EmbedMLP(int(max(cat.max(), cat_v.max())) + 1, emb_dim, X.shape[1], emb_init=emb_init)
    ys = float(np.std(y))
    c, x = torch.as_tensor(cat), torch.as_tensor(X, dtype=torch.float32)
    t = torch.as_tensor(y / ys, dtype=torch.float32)
    cv, xv = torch.as_tensor(cat_v), torch.as_tensor(X_v, dtype=torch.float32)
    tv = torch.as_tensor(y_v / ys, dtype=torch.float32)
    opt = torch.optim.Adam(m.parameters(), lr=lr)
    best, state, bad = np.inf, None, 0
    for _ in range(epochs):
        m.train()
        perm = torch.randperm(len(x), generator=g)
        for i in range(0, len(x), 1024):
            b = perm[i:i + 1024]
            opt.zero_grad()
            ((m(c[b], x[b]) - t[b]) ** 2).mean().backward()
            opt.step()
        m.eval()
        with torch.no_grad():
            v = float(((m(cv, xv) - tv) ** 2).mean())
        if v < best - 1e-7:
            best, state, bad = v, copy.deepcopy(m.state_dict()), 0
        else:
            bad += 1
            if bad >= patience:
                break
    m.load_state_dict(state)
    m.y_scale = ys
    return m
