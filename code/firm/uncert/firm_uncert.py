"""firm.uncert -- predictive distributions, scoring rules and conformal intervals (Book 12, chapter 11).

A forecast of a return is a distribution, and the firm scores it as one: the pinball loss for quantiles, the continuous
ranked probability score for whole distributions, and interval coverage. Networks that output a Gaussian or a mixture
of Gaussians are trained by their negative log-likelihood; seed ensembles split the predictive variance into an
aleatoric part (the members' average variance) and an epistemic part (their disagreement). Conformal prediction turns
any point forecast and any score into intervals with a coverage guarantee under exchangeability, and its adaptive
version keeps coverage when the data drift.

API (stable):
    pinball(y, q, alpha)                        mean pinball (quantile) loss of quantile forecasts q at level alpha
    crps_gaussian(y, mu, sigma)                 mean CRPS of Gaussian forecasts (closed form)
    crps_quantiles(y, Q, alphas)                CRPS approximated by twice the average pinball loss over a quantile grid
    coverage(y, lo, hi)                         share of y inside [lo, hi]
    GaussNet(p, hidden) / MDN(p, K, hidden)     torch networks; fit_nll(net, X, y, Xv, yv, seed, ...) trains either
    predict_gauss(net, X) -> (mu, sigma)        predict_mdn(net, X) -> (weights, mus, sigmas)
    mdn_quantile(w, m, s, alpha)                a quantile of a Gaussian mixture, by bisection
    ensemble_split(mus, sigmas) -> (mu, aleatoric var, epistemic var)
    split_conformal(scores, alpha) -> q         the ceil((n + 1)(1 - alpha))-th smallest calibration score
    adaptive_conformal(scores, alpha, gamma, window) -> (thresholds, errors)   online alpha_t (Gibbs and Candes)
"""
from __future__ import annotations

import copy
import math

import numpy as np
import torch
from torch import nn


def pinball(y, q, alpha):
    d = np.asarray(y) - np.asarray(q)
    return float(np.mean(np.maximum(alpha * d, (alpha - 1) * d)))


def crps_gaussian(y, mu, sigma):
    from scipy.stats import norm

    z = (np.asarray(y) - mu) / sigma
    return float(np.mean(sigma * (z * (2 * norm.cdf(z) - 1) + 2 * norm.pdf(z) - 1 / math.sqrt(math.pi))))


def crps_quantiles(y, Q, alphas):
    return 2.0 * float(np.mean([pinball(y, Q[:, j], a) for j, a in enumerate(alphas)]))


def coverage(y, lo, hi):
    y = np.asarray(y)
    return float(np.mean((y >= lo) & (y <= hi)))


class GaussNet(nn.Module):
    def __init__(self, p, hidden=(32, 16)):
        super().__init__()
        layers, d = [], p
        for h in hidden:
            layers += [nn.Linear(d, h), nn.ReLU()]
            d = h
        self.body = nn.Sequential(*layers)
        self.out = nn.Linear(d, 2)

    def forward(self, x):
        o = self.out(self.body(x))
        return o[:, 0], o[:, 1]                                          # mean, log variance

    def nll(self, x, y):
        m, lv = self(x)
        return (0.5 * (lv + (y - m) ** 2 / lv.exp())).mean()


class MDN(nn.Module):
    def __init__(self, p, K=2, hidden=(32, 16)):
        super().__init__()
        layers, d = [], p
        for h in hidden:
            layers += [nn.Linear(d, h), nn.ReLU()]
            d = h
        self.body = nn.Sequential(*layers)
        self.K = K
        self.out = nn.Linear(d, 3 * K)
        self.spread = torch.linspace(-1.0, 1.0, K) if K > 1 else torch.zeros(1)

    def reset_parameters(self):
        """Component means start spread over [-1, 1] (standardised units): started together, the components tend to
        collapse into one broad Gaussian."""
        with torch.no_grad():
            self.out.bias[self.K:2 * self.K] = self.spread

    def forward(self, x):
        o = self.out(self.body(x))
        return torch.log_softmax(o[:, :self.K], 1), o[:, self.K:2 * self.K], o[:, 2 * self.K:]   # log w, means, log sd

    def nll(self, x, y):
        lw, m, ls = self(x)
        lp = lw - ls - 0.5 * ((y[:, None] - m) / ls.exp()) ** 2
        return -torch.logsumexp(lp, 1).mean()


def fit_nll(net, X, y, Xv, yv, seed=1, lr=1e-3, epochs=40, patience=5, batch=512):
    """Train by negative log-likelihood on standardised targets; the target scale is stored on the network."""
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed)
    for mod in list(net.modules())[::-1]:                               # initial weights from the seed, whatever the
        if hasattr(mod, "reset_parameters"):                            # global generator did before; layers first,
            mod.reset_parameters()                                      # then the network's own initialisation
    g = torch.Generator().manual_seed(seed)
    net.ys = float(np.std(y))
    Xt, yt = torch.as_tensor(X, dtype=torch.float32), torch.as_tensor(y / net.ys, dtype=torch.float32)
    Xvt, yvt = torch.as_tensor(Xv, dtype=torch.float32), torch.as_tensor(yv / net.ys, dtype=torch.float32)
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    best, state, bad = np.inf, None, 0
    for _ in range(epochs):
        net.train()
        perm = torch.randperm(len(Xt), generator=g)
        for i in range(0, len(Xt), batch):
            b = perm[i:i + batch]
            opt.zero_grad()
            net.nll(Xt[b], yt[b]).backward()
            opt.step()
        net.eval()
        with torch.no_grad():
            v = float(net.nll(Xvt, yvt))
        if v < best - 1e-6:
            best, state, bad = v, copy.deepcopy(net.state_dict()), 0
        else:
            bad += 1
            if bad >= patience:
                break
    net.load_state_dict(state)
    return net


def predict_gauss(net, X):
    with torch.no_grad():
        m, lv = net(torch.as_tensor(X, dtype=torch.float32))
    return m.numpy() * net.ys, np.exp(0.5 * lv.numpy()) * net.ys


def predict_mdn(net, X):
    with torch.no_grad():
        lw, m, ls = net(torch.as_tensor(X, dtype=torch.float32))
    return np.exp(lw.numpy()), m.numpy() * net.ys, np.exp(ls.numpy()) * net.ys


def mdn_quantile(w, m, s, alpha, iters=60):
    from scipy.stats import norm

    lo = (m - 8 * s).min(axis=1)
    hi = (m + 8 * s).max(axis=1)
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        c = (w * norm.cdf((mid[:, None] - m) / s)).sum(axis=1)
        lo, hi = np.where(c < alpha, mid, lo), np.where(c < alpha, hi, mid)
    return 0.5 * (lo + hi)


def ensemble_split(mus, sigmas):
    mus, sig2 = np.asarray(mus), np.asarray(sigmas) ** 2
    return mus.mean(axis=0), sig2.mean(axis=0), mus.var(axis=0)


def split_conformal(scores, alpha):
    s = np.sort(np.asarray(scores))
    n = len(s)
    k = min(n, math.ceil((n + 1) * (1 - alpha)))
    return float(s[k - 1])


def adaptive_conformal(scores, alpha, gamma=0.005, window=500, start=None):
    """Online conformal thresholds: at each step t the threshold is the (1 - alpha_t) quantile of the last `window`
    scores; after seeing whether score t exceeded it, alpha_{t+1} = alpha_t + gamma (alpha - err_t)."""
    scores = np.asarray(scores)
    a = alpha
    th, err = np.empty(len(scores)), np.empty(len(scores))
    hist = list(start) if start is not None else []
    for t, s in enumerate(scores):
        pool = np.asarray(hist[-window:])
        q = np.quantile(pool, min(max(1 - a, 0.0), 1.0)) if len(pool) else np.inf
        th[t] = q
        err[t] = float(s > q)
        a = a + gamma * (alpha - err[t])
        hist.append(s)
    return th, err
