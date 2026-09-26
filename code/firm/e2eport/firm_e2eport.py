"""firm.e2eport -- from prediction to portfolio: predict-then-optimise against decision-focused learning (Book 12,
chapter 22).

A mean-variance layer with a quadratic trading-cost proxy, in closed form for a diagonal risk model, so that it can sit
inside a network and be differentiated: w = (mu + 2 kappa w_prev) / (gamma sigma^2 + 2 kappa), per name, zero for names
outside the tradeable universe. Forecasts are linear in characteristics. Three ways to choose the forecast's
coefficients: least squares on every name (predict, then optimise), least squares on the tradeable names only, and
decision-focused learning, which maximises the Sharpe ratio of the portfolio's returns net of linear costs through the
layer (starting from least squares). A parametric portfolio policy (Brandt, Santa-Clara and Valkanov) maps
characteristics to weights directly, without the layer. The closed-form layer is checked against Book 7's
firm.portcons optimiser in tests.

API (stable):
    char_panel(seed, T, N, K, n_signal, phi) -> dict(X (T, N, K), R (T, N), tradeable (N,))
    mv_layer(mu, w_prev, kappa, gamma, sigma)            numpy or torch, elementwise
    run(b, X, R, tradeable, cost, gamma, sigma, policy) -> dict(net Sharpe, gross Sharpe, turnover)
    least_squares(X, R, rows) -> b
    train_decision(X, R, tradeable, init, policy, epochs, lr, window, seed, cost, gamma, sigma) -> b
"""
from __future__ import annotations

import math

import numpy as np
import torch

COST, GAMMA, SIGMA = 0.0005, 20.0, 0.03


def char_panel(seed=0, T=1500, N=200, K=4, n_noise=0, phi=0.9):
    """Characteristics follow AR(1) with coefficient phi. Half the names are tradeable, and in them only the second
    characteristic predicts returns (0.08% a period per unit); in the other half only the first does, strongly (0.3%).
    Returns have 3% of noise per period. n_noise extra characteristics predict nothing."""
    rng = np.random.default_rng(seed)
    K = K + n_noise
    X = np.zeros((T, N, K))
    X[0] = rng.standard_normal((N, K))
    for t in range(1, T):
        X[t] = phi * X[t - 1] + math.sqrt(1 - phi**2) * rng.standard_normal((N, K))
    tradeable = np.arange(N) < N // 2
    mu = np.where(tradeable, 0.0008 * X[:, :, 1], 0.003 * X[:, :, 0])
    return {"X": X, "R": mu + SIGMA * rng.standard_normal((T, N)), "tradeable": tradeable}


def mv_layer(mu, w_prev, kappa, gamma=GAMMA, sigma=SIGMA):
    """argmax_w mu w - gamma/2 sigma^2 w^2 - kappa (w - w_prev)^2, name by name."""
    return (mu + 2 * kappa * w_prev) / (gamma * sigma**2 + 2 * kappa)


def _weights(policy, mu, w, cost, gamma, sigma):
    if policy == "mv":
        return mv_layer(mu, w, cost, gamma, sigma)
    return mu / (gamma * sigma**2)                                       # parametric policy: no smoothing


def run(b, X, R, tradeable, cost=COST, gamma=GAMMA, sigma=SIGMA, policy="mv"):
    """Trade the tradeable names period by period; net returns pay cost times the absolute change in weights."""
    T, N, _ = X.shape
    w = np.zeros(N)
    net, gross, turn = np.empty(T), np.empty(T), np.empty(T)
    for t in range(T):
        wn = np.where(tradeable, _weights(policy, X[t] @ b, w, cost, gamma, sigma), 0.0)
        gross[t] = wn @ R[t]
        turn[t] = np.abs(wn - w).sum()
        net[t] = gross[t] - cost * turn[t]
        w = wn
    sr = lambda x: float(x.mean() / x.std() * math.sqrt(52))            # noqa: E731
    return {"net": sr(net), "gross": sr(gross), "turnover": float(turn.mean())}


def least_squares(X, R, rows=None):
    Xs, Rs = (X, R) if rows is None else (X[:, rows], R[:, rows])
    return np.linalg.lstsq(Xs.reshape(-1, X.shape[2]), Rs.reshape(-1), rcond=None)[0]


def train_decision(X, R, tradeable, init, policy="mv", epochs=20, lr=0.02, window=100, seed=0, cost=COST,
                   gamma=GAMMA, sigma=SIGMA):
    """Maximise the Sharpe ratio of net returns over windows of `window` periods by gradient ascent through the
    portfolio rule; coefficients in units of 0.1%."""
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed)
    Xt = torch.as_tensor(X[:, tradeable], dtype=torch.float32)
    Rt = torch.as_tensor(R[:, tradeable], dtype=torch.float32)
    th = torch.tensor(np.asarray(init) * 1e3, dtype=torch.float32, requires_grad=True)
    opt = torch.optim.Adam([th], lr=lr)
    for _ in range(epochs):
        for s in range(0, len(Xt) - window + 1, window):
            w = torch.zeros(Xt.shape[1])
            nets = []
            for t in range(s, s + window):
                wn = _weights(policy, Xt[t] @ (1e-3 * th), w, cost, gamma, sigma)
                nets.append(wn @ Rt[t] - cost * torch.abs(wn - w).sum())
                w = wn
            n = torch.stack(nets)
            loss = -n.mean() / n.std()
            opt.zero_grad()
            loss.backward()
            opt.step()
    return 1e-3 * th.detach().numpy()
