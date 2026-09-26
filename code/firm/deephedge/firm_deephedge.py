"""firm.deephedge -- deep hedging, differential-learning surrogates and calibration networks (Book 12, chapter 19).

Deep hedging (Buehler, Gonon, Teichmann and Wood): a network chooses the hedge at each date from what is observable,
and is trained on simulated paths to minimise a convex risk measure of the hedged P&L after proportional costs. The
policy used here is the no-transaction band network (Imaki and co-authors): the network outputs a band and the new
holding is the old one clipped into it, so the no-trade region is explicit. Baselines: Black-Scholes delta, the
Whalley-Wilmott band, no hedge. Risk measures: entropic and expected shortfall; the indifference price is the cash that
makes the seller's risk zero. A surrogate network learns a pricer from samples, with differential labels
(Huge and Savine) or without; a calibration network learns the inverse map from implied volatilities to parameters.

API (stable):
    heston_paths(model, s0, T, n, paths, seed) -> (paths, n + 1) spots on a regular grid (Book 5's firm.heston)
    BandNet(hidden) ; hedge_pnl(policy, S, K, T, cost) -> terminal P&L of selling the call and hedging (torch)
    entropic(X, lam), expected_shortfall(X, alpha)       risk of a P&L sample (to be minimised)
    train_hedge(S, K, T, cost, risk, seed, steps, ...) -> BandNet
    bs_policy(sigma, K, T), ww_policy(sigma, K, T, cost, lam), no_hedge   baseline policies (same interface)
    band(policy, t, s, K) -> (lower, upper) of a band policy at one state
    SurrogateNet ; fit_surrogate(X, y, dy, differential, seed, ...) -> net   dy: pathwise derivative labels
    fit_calibrator(vols, params, seed, ...) -> net ; the inverse map from an implied-volatility grid to parameters
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np
import torch
from torch import nn

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "heston"))
import firm_heston as fh  # noqa: E402


def heston_paths(model, s0=100.0, T=1 / 12, n=21, paths=20000, seed=0):
    times = np.linspace(T / n, T, n)
    return fh.simulate_paths(model, s0, times, int(round(n / T)), paths, seed)


def _ncdf(x):
    return 0.5 * (1 + torch.erf(x / math.sqrt(2.0)))


def _bs_delta(s, K, tau, sigma):
    d1 = (torch.log(s / K) + 0.5 * sigma**2 * tau) / (sigma * torch.sqrt(tau))
    return _ncdf(d1)


def _bs_gamma(s, K, tau, sigma):
    d1 = (torch.log(s / K) + 0.5 * sigma**2 * tau) / (sigma * torch.sqrt(tau))
    return torch.exp(-0.5 * d1**2) / math.sqrt(2 * math.pi) / (s * sigma * torch.sqrt(tau))


class BandNet(nn.Module):
    """Inputs (time to maturity / T, log-moneyness); outputs a band [lower, upper] in delta units. The new holding is
    the previous one clipped into the band."""

    def __init__(self, hidden=(32, 32)):
        super().__init__()
        layers, d = [], 2
        for h in hidden:
            layers += [nn.Linear(d, h), nn.ReLU()]
            d = h
        self.net = nn.Sequential(*layers, nn.Linear(d, 2))

    def forward(self, tau_frac, logm, prev):
        o = self.net(torch.stack([tau_frac, logm], -1))
        centre, half = torch.sigmoid(o[..., 0]), nn.functional.softplus(o[..., 1] - 3.0)
        return torch.minimum(torch.maximum(prev, centre - half), centre + half), centre - half, centre + half


def hedge_pnl(policy, S, K, T, cost):
    """Selling one call and hedging at each of the n dates before maturity: the terminal P&L (without the premium)
    = sum_k delta_k (S_{k+1} - S_k) - cost * sum_k |delta_k - delta_{k-1}| S_k - cost * |delta_{n-1}| S_n - (S_n - K)+.
    policy(tau_frac, logm, prev) -> (holding, lower, upper)."""
    S = torch.as_tensor(S, dtype=torch.float32)
    n = S.shape[1] - 1
    prev = torch.zeros(S.shape[0])
    pnl = torch.zeros(S.shape[0])
    for k in range(n):
        tau_frac = torch.full_like(prev, (n - k) / n)
        h, _, _ = policy(tau_frac, torch.log(S[:, k] / K), prev)
        pnl = pnl + h * (S[:, k + 1] - S[:, k]) - cost * torch.abs(h - prev) * S[:, k]
        prev = h
    pnl = pnl - cost * torch.abs(prev) * S[:, n] - torch.clamp(S[:, n] - K, min=0.0)
    return pnl


def entropic(X, lam=1.0):
    """(1 / lam) log E exp(-lam X): the entropic risk measure; its value is the indifference price when X is the
    seller's hedged P&L without the premium."""
    return (torch.logsumexp(-lam * X, 0) - math.log(len(X))) / lam


def expected_shortfall(X, alpha=0.95):
    """Mean of the worst (1 - alpha) share of outcomes, as a loss."""
    k = max(1, int(round((1 - alpha) * len(X))))
    return -torch.topk(X, k, largest=False).values.mean()


def train_hedge(S, K, T, cost, risk="entropic", seed=0, steps=300, batch=4096, lr=5e-3, lam=1.0, alpha=0.95,
                hidden=(32, 32)):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed)
    net = BandNet(hidden)
    g = torch.Generator().manual_seed(seed)
    S = torch.as_tensor(S, dtype=torch.float32)
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    for _ in range(steps):
        idx = torch.randint(len(S), (batch,), generator=g)
        X = hedge_pnl(net, S[idx], K, T, cost)
        loss = entropic(X, lam) if risk == "entropic" else expected_shortfall(X, alpha)
        opt.zero_grad()
        loss.backward()
        opt.step()
    return net


def bs_policy(sigma, K, T):
    """Rebalance to the Black-Scholes delta at every date."""
    def policy(tau_frac, logm, prev):
        d = _bs_delta(K * torch.exp(logm), K, tau_frac * T, sigma)
        return d, d, d
    return policy


def ww_policy(sigma, K, T, cost, lam):
    """Whalley-Wilmott: trade to the nearer edge of a band around the delta, of half-width
    (3 cost S Gamma^2 / (2 lam))^(1/3) (zero interest)."""
    def policy(tau_frac, logm, prev):
        s = K * torch.exp(logm)
        tau = tau_frac * T
        d, gam = _bs_delta(s, K, tau, sigma), _bs_gamma(s, K, tau, sigma)
        half = (1.5 * cost * s * gam**2 / lam) ** (1 / 3)
        return torch.minimum(torch.maximum(prev, d - half), d + half), d - half, d + half
    return policy


def no_hedge(tau_frac, logm, prev):
    z = torch.zeros_like(prev)
    return z, z, z


def band(policy, tau_frac, s, K):
    with torch.no_grad():
        _, lo, hi = policy(torch.tensor([tau_frac]), torch.tensor([math.log(s / K)]), torch.tensor([0.0]))
    return float(lo), float(hi)


# ---------------------------------------------------------------------------------------------------- surrogates
class SurrogateNet(nn.Module):
    def __init__(self, d_in, hidden=(64, 64)):
        super().__init__()
        layers, d = [], d_in
        for h in hidden:
            layers += [nn.Linear(d, h), nn.Softplus()]
            d = h
        self.net = nn.Sequential(*layers, nn.Linear(d, 1))

    def forward(self, x):
        return self.net(x)[:, 0]


def fit_surrogate(X, y, dy=None, differential=False, seed=0, epochs=400, lr=5e-3, weight=1.0, hidden=(64, 64)):
    """Fit price labels y (and, if differential, derivative labels dy with respect to the first input) by mean
    squared error, the derivative of the network taken by automatic differentiation (Huge and Savine)."""
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed)
    net = SurrogateNet(X.shape[1], hidden)
    Xt = torch.as_tensor(X, dtype=torch.float32)
    yt = torch.as_tensor(y, dtype=torch.float32)
    dyt = None if dy is None else torch.as_tensor(dy, dtype=torch.float32)
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    for _ in range(epochs):
        x = Xt.clone().requires_grad_(differential)
        p = net(x)
        loss = ((p - yt) ** 2).mean()
        if differential:
            dp = torch.autograd.grad(p.sum(), x, create_graph=True)[0][:, 0]
            loss = loss + weight * ((dp - dyt) ** 2).mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
    return net


def surrogate_values(net, X):
    x = torch.as_tensor(X, dtype=torch.float32).requires_grad_(True)
    p = net(x)
    d = torch.autograd.grad(p.sum(), x)[0][:, 0]
    return p.detach().numpy(), d.numpy()


def fit_calibrator(vols, params, seed=0, epochs=2000, lr=3e-3, hidden=(64, 64)):
    """The inverse map: an implied-volatility grid (flattened) to model parameters (standardised), by least squares."""
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed)
    X = torch.as_tensor(vols, dtype=torch.float32)
    P = np.asarray(params, float)
    mu, sd = P.mean(0), P.std(0)
    Y = torch.as_tensor((P - mu) / sd, dtype=torch.float32)
    layers, d = [], X.shape[1]
    for h in hidden:
        layers += [nn.Linear(d, h), nn.ReLU()]
        d = h
    net = nn.Sequential(*layers, nn.Linear(d, Y.shape[1]))
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    for _ in range(epochs):
        loss = ((net(X) - Y) ** 2).mean()
        opt.zero_grad()
        loss.backward()
        opt.step()

    def predict(v):
        with torch.no_grad():
            return net(torch.as_tensor(v, dtype=torch.float32)).numpy() * sd + mu
    return predict
