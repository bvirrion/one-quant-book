"""firm.genmkt -- generators of synthetic market data and the tests that judge them (Book 12, chapter 16).

Generators of return windows (a block bootstrap, a GARCH(1,1) model with Student-t shocks, a variational autoencoder,
a generative adversarial network and a denoising diffusion model), all producing arrays of shape (n, L) of standardised
daily returns; a stylised-fact scorecard; the classifier two-sample test; train-on-synthetic test-on-real; and a
nearest-neighbour memorisation check. Networks are small multilayer perceptrons on windows, trained on one thread.

API (stable):
    real_index(n_days, seed) -> dict(r, crashes)          daily index returns: GJR-GARCH-t, planted crashes, momentum
    windows(r, L, step) -> (n, L)                          overlapping windows
    block_bootstrap(r, n, L, block, seed)                  windows cut from a series resampled in blocks
    fit_garch(r) -> params; garch_windows(params, n, L, seed, burn)
    VAE(L, latent, hidden), GAN(L, noise, hidden), Diffusion(L, T, hidden): .fit(W, steps, seed), .sample(n, seed)
    facts(W) -> dict of statistics; scorecard(W) -> {fact: passes}; CHECKS the six stylised-fact rules
    c2st(W_a, W_b, groups_a, groups_b, seed) -> held-out accuracy of a classifier telling the two apart
    window_features(W) -> (n, k) features of the first L-1 days; tstr(W_train, W_test) -> (IC, Sharpe of the sign rule)
    nn_distance(W_gen, W_train) -> distances to the nearest training window
"""
from __future__ import annotations

import math

import numpy as np
import torch
from torch import nn


def real_index(n_days=7560, seed=0):
    """GJR-GARCH(1,1) with Student-t(4) shocks, six planted crashes (a -8 to -11 sigma day and a volatility spike),
    and time-series momentum: the conditional mean is 0.1 sigma_t times the sign of the last 20 days' return."""
    rng = np.random.default_rng(seed)
    omega, alpha, gamma, beta = 0.02, 0.03, 0.10, 0.88
    crashes = sorted(rng.choice(np.arange(500, n_days - 100), 6, replace=False).tolist())
    r = np.zeros(n_days)
    h = omega / (1 - alpha - gamma / 2 - beta)
    z = rng.standard_t(4, n_days) / math.sqrt(2.0)
    for t in range(n_days):
        mom = np.sign(r[max(0, t - 20):t].sum()) if t > 20 else 0.0
        eps = math.sqrt(h) * z[t]
        if t in crashes:
            eps = -math.sqrt(h) * rng.uniform(8.0, 11.0)
        r[t] = 0.02 + 0.1 * math.sqrt(h) * mom + eps
        h = omega + (alpha + gamma * (eps < 0)) * eps**2 + beta * h
    return {"r": r / 100.0, "crashes": crashes}


def windows(r, L=32, step=1):
    idx = np.arange(0, len(r) - L + 1, step)
    return np.stack([r[i:i + L] for i in idx])


def block_bootstrap(r, n, L=32, block=20, seed=0):
    rng = np.random.default_rng(seed)
    out = np.empty((n, L))
    for k in range(n):
        path = []
        while len(path) < L:
            s = int(rng.integers(0, len(r) - block))
            path.extend(r[s:s + block])
        out[k] = path[:L]
    return out


def fit_garch(r):
    """GARCH(1,1) with Student-t shocks by maximum likelihood (scipy); returns (mu, omega, alpha, beta, nu)."""
    from scipy.optimize import minimize
    from scipy.special import gammaln

    x = np.asarray(r) * 100

    def nll(p):
        mu, om, a, b, nu = p
        if om <= 0 or a < 0 or b < 0 or a + b >= 0.999 or nu <= 2.1:
            return 1e10
        e = x - mu
        h = np.empty_like(x)
        h[0] = e.var()
        for t in range(1, len(x)):
            h[t] = om + a * e[t - 1] ** 2 + b * h[t - 1]
        s2 = h * (nu - 2) / nu
        ll = gammaln((nu + 1) / 2) - gammaln(nu / 2) - 0.5 * np.log(np.pi * nu * s2) \
            - (nu + 1) / 2 * np.log1p(e**2 / (nu * s2))
        return -ll.sum()

    res = minimize(nll, [0.03, 0.02, 0.08, 0.9, 6.0], method="Nelder-Mead", options={"maxiter": 3000, "xatol": 1e-5,
                                                                                      "fatol": 1e-4})
    return tuple(res.x)


def garch_windows(params, n, L=32, seed=0, burn=200):
    mu, om, a, b, nu = params
    rng = np.random.default_rng(seed)
    out = np.empty((n, L))
    for k in range(n):
        h = om / (1 - a - b)
        e = 0.0
        path = []
        for t in range(burn + L):
            h = om + a * e**2 + b * h
            e = math.sqrt(h) * rng.standard_t(nu) * math.sqrt((nu - 2) / nu)
            if t >= burn:
                path.append(mu + e)
        out[k] = np.array(path) / 100
    return out


# ---------------------------------------------------------------------------------------------------- networks
def _mlp(d_in, hidden, d_out):
    layers, d = [], d_in
    for h in hidden:
        layers += [nn.Linear(d, h), nn.SiLU()]
        d = h
    return nn.Sequential(*layers, nn.Linear(d, d_out))


def _seed(seed, *mods):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed)
    for m in mods:
        for x in m.modules():
            if hasattr(x, "reset_parameters") and x is not m:
                x.reset_parameters()
    return torch.Generator().manual_seed(seed)


class _Scaled:
    """Networks work on windows divided by the training windows' standard deviation."""

    def _set_scale(self, W):
        self.scale = float(np.std(W))
        return torch.as_tensor(W / self.scale, dtype=torch.float32)


class VAE(_Scaled):
    def __init__(self, L=32, latent=4, hidden=(64, 64)):
        self.L, self.latent = L, latent
        self.enc = _mlp(L, hidden, 2 * latent)
        self.dec = _mlp(latent, hidden[::-1], 2 * L)                   # mean and log variance of each day

    def fit(self, W, steps=3000, seed=0, batch=256, lr=2e-3):
        g = _seed(seed, self.enc, self.dec)
        X = self._set_scale(W)
        opt = torch.optim.Adam(list(self.enc.parameters()) + list(self.dec.parameters()), lr=lr)
        for _ in range(steps):
            xb = X[torch.randint(len(X), (batch,), generator=g)]
            m, lv = self.enc(xb).chunk(2, -1)
            zb = m + torch.exp(0.5 * lv) * torch.randn(m.shape, generator=g)
            dm, dlv = self.dec(zb).chunk(2, -1)
            rec = 0.5 * (dlv + (xb - dm) ** 2 / dlv.exp()).sum(1)
            kl = 0.5 * (m**2 + lv.exp() - 1 - lv).sum(1)
            loss = (rec + kl).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
        return self

    def sample(self, n, seed=0):
        g = torch.Generator().manual_seed(seed)
        with torch.no_grad():
            dm, dlv = self.dec(torch.randn((n, self.latent), generator=g)).chunk(2, -1)
            x = dm + torch.exp(0.5 * dlv) * torch.randn(dm.shape, generator=g)
        return x.numpy() * self.scale


class GAN(_Scaled):
    def __init__(self, L=32, noise=16, hidden=(128, 128)):
        self.L, self.noise = L, noise
        self.G = _mlp(noise, hidden, L)
        self.D = _mlp(L, hidden, 1)

    def fit(self, W, steps=3000, seed=0, batch=256, lr=2e-4):
        g = _seed(seed, self.G, self.D)
        X = self._set_scale(W)
        oG = torch.optim.Adam(self.G.parameters(), lr=lr, betas=(0.5, 0.999))
        oD = torch.optim.Adam(self.D.parameters(), lr=lr, betas=(0.5, 0.999))
        bce = nn.BCEWithLogitsLoss()
        ones, zeros = torch.ones(batch, 1), torch.zeros(batch, 1)
        for _ in range(steps):
            xb = X[torch.randint(len(X), (batch,), generator=g)]
            fake = self.G(torch.randn((batch, self.noise), generator=g))
            lD = bce(self.D(xb), ones) + bce(self.D(fake.detach()), zeros)
            oD.zero_grad()
            lD.backward()
            oD.step()
            lG = bce(self.D(fake), ones)
            oG.zero_grad()
            lG.backward()
            oG.step()
        return self

    def sample(self, n, seed=0):
        g = torch.Generator().manual_seed(seed)
        with torch.no_grad():
            return self.G(torch.randn((n, self.noise), generator=g)).numpy() * self.scale


class Diffusion(_Scaled):
    """Denoising diffusion (Ho, Jain and Abbeel): noise the windows over T steps with a linear variance schedule, train
    a network to predict the noise from the noisy window and the step, and sample by running the chain backwards."""

    def __init__(self, L=32, T=100, hidden=(128, 128)):
        self.L, self.T = L, T
        self.net = _mlp(L + 1, hidden, L)
        self.beta = torch.linspace(1e-4, 0.05, T)
        self.abar = torch.cumprod(1 - self.beta, 0)

    def fit(self, W, steps=3000, seed=0, batch=256, lr=2e-3):
        g = _seed(seed, self.net)
        X = self._set_scale(W)
        opt = torch.optim.Adam(self.net.parameters(), lr=lr)
        for _ in range(steps):
            xb = X[torch.randint(len(X), (batch,), generator=g)]
            t = torch.randint(self.T, (batch,), generator=g)
            e = torch.randn(xb.shape, generator=g)
            ab = self.abar[t][:, None]
            xt = ab.sqrt() * xb + (1 - ab).sqrt() * e
            loss = ((self.net(torch.cat([xt, (t[:, None] + 0.5) / self.T], 1)) - e) ** 2).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
        return self

    def sample(self, n, seed=0):
        g = torch.Generator().manual_seed(seed)
        x = torch.randn((n, self.L), generator=g)
        with torch.no_grad():
            for t in range(self.T - 1, -1, -1):
                tt = torch.full((n, 1), (t + 0.5) / self.T)
                e = self.net(torch.cat([x, tt], 1))
                b, ab = self.beta[t], self.abar[t]
                x = (x - b / (1 - ab).sqrt() * e) / (1 - b).sqrt()
                if t > 0:
                    x = x + b.sqrt() * torch.randn(x.shape, generator=g)
        return x.numpy() * self.scale


# ---------------------------------------------------------------------------------------------------- judging
def _pooled_ac(W, lag, f=lambda x: x):
    a, b = f(W[:, :-lag]).ravel(), f(W[:, lag:]).ravel()
    return float(np.corrcoef(a, b)[0, 1])


def facts(W):
    """Stylised facts computed within windows (pooled across windows)."""
    x = W.ravel()
    z = (x - x.mean()) / x.std()
    agg = W[:, :20].sum(1)
    za = (agg - agg.mean()) / agg.std()
    return {"kurtosis": float(np.mean(z**4) - 3), "skewness": float(np.mean(z**3)),
            "ac1": _pooled_ac(W, 1), "abs ac1": _pooled_ac(W, 1, np.abs),
            "abs ac10": _pooled_ac(W, 10, np.abs),
            "leverage": float(np.corrcoef(W[:, :-1].ravel(), np.abs(W[:, 1:]).ravel())[0, 1]),
            "kurtosis 20d": float(np.mean(za**4) - 3)}


CHECKS = {"heavy tails": lambda f: f["kurtosis"] > 5.0,
          "no linear autocorrelation": lambda f: abs(f["ac1"]) < 0.1,
          "volatility clustering": lambda f: f["abs ac1"] > 0.1 and f["abs ac10"] > 0.05,
          "leverage effect": lambda f: f["leverage"] < -0.03,
          "gain-loss asymmetry": lambda f: f["skewness"] < -0.1,
          "aggregational Gaussianity": lambda f: f["kurtosis 20d"] < 0.5 * f["kurtosis"]}


def scorecard(W):
    f = facts(W)
    return {k: bool(c(f)) for k, c in CHECKS.items()}


def window_features(W):
    """Features of the first L-1 days of each window, used both to tell windows apart and to predict the last day."""
    x = W[:, :-1]
    s = x.std(1) + 1e-12
    return np.column_stack([x[:, -1] / s, x[:, -5:].sum(1) / s, x[:, -20:].sum(1) / s, np.sign(x[:, -20:].sum(1)),
                            s, np.abs(x).max(1) / s, ((x / s[:, None]) ** 4).mean(1), (x / s[:, None]).min(1)])


def c2st(A, B, groups_a=None, groups_b=None, seed=0):
    """Classifier two-sample test (Lopez-Paz and Oquab): a gradient-boosted classifier on window features, trained on
    half of each sample and scored on the other half; 0.5 means indistinguishable. Overlapping windows of a real series
    must be split by time block (groups), or the classifier recognises a test window's neighbours."""
    import lightgbm as lgb

    rng = np.random.default_rng(seed)

    def halves(W, groups):
        if groups is None:
            idx = rng.permutation(len(W))
            return W[idx[: len(W) // 2]], W[idx[len(W) // 2:]]
        g = np.asarray(groups)
        return W[g % 2 == 0], W[g % 2 == 1]

    (a1, a2), (b1, b2) = halves(A, groups_a), halves(B, groups_b)
    n1, n2 = min(len(a1), len(b1)), min(len(a2), len(b2))
    a1, b1, a2, b2 = a1[:n1], b1[:n1], a2[:n2], b2[:n2]

    def feats(W):
        return np.column_stack([window_features(W), np.sort(W / W.std(1, keepdims=True), 1)[:, [0, 1, -2, -1]],
                                np.abs(W).mean(1)])

    Xtr, ytr = np.vstack([feats(a1), feats(b1)]), np.r_[np.zeros(n1), np.ones(n1)]
    Xte, yte = np.vstack([feats(a2), feats(b2)]), np.r_[np.zeros(n2), np.ones(n2)]
    m = lgb.LGBMClassifier(n_estimators=200, learning_rate=0.05, num_leaves=15, n_jobs=1, num_threads=1, verbose=-1,
                           deterministic=True, random_state=seed).fit(Xtr, ytr)
    return float(np.mean((m.predict_proba(Xte)[:, 1] > 0.5) == yte))


def tstr(W_train, W_test):
    """Fit a linear forecast of each window's last day from its features on W_train; score on W_test: the rank IC and
    the annualised Sharpe ratio of trading the sign of the forecast."""
    from scipy.stats import spearmanr

    Xa, ya = window_features(W_train), W_train[:, -1]
    Xa1 = np.column_stack([np.ones(len(Xa)), Xa])
    b = np.linalg.lstsq(Xa1, ya, rcond=None)[0]
    Xb = np.column_stack([np.ones(len(W_test)), window_features(W_test)])
    f = Xb @ b
    pnl = np.sign(f - np.median(f)) * W_test[:, -1]
    return float(spearmanr(f, W_test[:, -1])[0]), float(pnl.mean() / pnl.std() * math.sqrt(252))


def nn_distance(W_gen, W_train, chunk=500):
    """Euclidean distance from each generated window to its nearest training window (in units of the training
    returns' standard deviation)."""
    s = W_train.std()
    A, B = W_gen / s, W_train / s
    b2 = (B**2).sum(1)
    out = []
    for i in range(0, len(A), chunk):
        a = A[i:i + chunk]
        d2 = (a**2).sum(1)[:, None] + b2[None] - 2 * a @ B.T
        out.append(np.sqrt(np.maximum(d2.min(1), 0)))
    return np.concatenate(out)
